# Design: Atomic Operations and Invariants in Gobra

This document describes the design of atomic operations and invariants in Gobra,
a verifier for Go programs. This feature enables sound modular reasoning about
concurrent programs using separation logic and atomic specifications.

## Motivation

Verifying concurrent Go programs requires reasoning about shared mutable state.
The standard Go concurrency model provides atomics (`sync/atomic`), mutexes, and
channels, but a verifier needs a formal framework to reason about *when* shared
state may be accessed and *what invariants* it satisfies.

This feature introduces three complementary concepts:

1. **Atomic methods** — abstract methods whose effects occur at a single
   linearization point.
2. **Invariants** — predicates that are permanently shared with all threads once
   established.
3. **Critical regions** — scoped blocks that temporarily open one invariant
   to perform exactly one atomic operation.

Together they give Gobra a light-weight way to verify concurrent programs
without requiring full concurrent separation logic: the programmer annotates
which operations are atomic, declares the invariants that protect shared state,
and Gobra statically checks that every access to shared state goes through a
properly guarded critical region.

## Core Concepts

### Atomic Methods

An *atomic method* is an abstract (body-less) function or method marked with
`atomic`. The annotation asserts that, from the point of view of any thread
observing the execution, the entire specified effect happens instantaneously —
there is no intermediate state visible to other threads.

```gobra
// CAS atomically compares *x with oldv.
// If equal, it sets *x to newv and returns true; otherwise leaves *x unchanged.
preserves acc(x)
ensures   b ==> *x == newv && old(*x) == oldv
ensures   !b ==> *x == old(*x) && old(*x) != oldv
decreases
atomic func CAS(x *int, oldv int, newv int) (b bool)

// Get atomically reads *x.
preserves acc(x)
decreases
atomic func Get(x *int) int
```

**Restrictions on atomic methods:**

- An atomic method must be *abstract* (no body). Gobra does not verify atomicity
  of concrete implementations; the annotation is trusted for abstract methods and
  checked at interface implementations (see below).
- An atomic method must have a termination measure (`decreases`). This ensures
  that the atomic step itself terminates, a necessary condition for linearizability
  reasoning.
- Ghost functions may **not** be marked `atomic`. Atomicity is a property of
  executable code; ghost operations exist only in the proof and have no run-time
  counterpart to linearize.

**Interface methods.** Interface methods may also be declared `atomic`:

```gobra
type AtomicInt interface {
    decreases
    atomic
    Get() int

    decreases
    atomic
    CAS(oldv int, newv int) (b bool)
}
```

When a concrete type asserts that it implements such an interface, Gobra checks
that every `atomic` interface member is implemented by an `atomic` function.
Non-atomic implementations of atomic interface members are rejected.

```gobra
type T1 struct{}

decreases
atomic func (t T1) Get() int      // OK

decreases
func (t T1) CAS(o, n int) bool    // not atomic — would make T1 implements AtomicInt fail
```

### Invariants

An *invariant* is a predicate that has been permanently transferred to the
shared heap. Once established, the predicate instance can never be exclusively
owned by a single thread again; instead, all threads may open it inside a
critical region.

**Establishing an invariant.** The built-in ghost function `EstablishInvariant`
converts exclusive predicate ownership into an invariant:

```gobra
ghost
requires p()
ensures  Invariant(p)
decreases
func EstablishInvariant(p pred())
```

The caller gives up the predicate instance `p()` and receives `Invariant(p)` in
return. `Invariant(p)` is a duplicable resource (it can be shared freely) that
acts as a *token* granting the right to open the invariant inside a critical
region.

**Modular visibility.** `Invariant(p)` is a normal resource in Gobra's permission
system. A function that needs to open invariant `p` simply requires
`Invariant(p)` in its precondition. Callers propagate the token by passing it
through their own pre/postconditions. There is no global registry of invariants;
the modular structure mirrors standard separation logic.

```gobra
// callTryCAS establishes Own as an invariant and then passes
// the token to tryCAS.
decreases
func callTryCAS() {
    x@ := 1
    fold Own!<&x!>()
    EstablishInvariant(Own!<&x!>)   // gives up Own(&x), gains Invariant(Own!<&x!>)
    tryCAS(&x)                       // tryCAS requires Invariant(Own!<&x!>)
}
```

**Invariants are permanent.** There is currently no way to "un-establish" an
invariant. This is intentional: allowing invariants to be revoked would
complicate the concurrency model and is not needed for the target use cases.

### Critical Regions

A *critical region* temporarily opens one invariant to perform a single atomic
operation. The syntax is:

```gobra
critical P!<args!> (
    // ghost setup
    // exactly one atomic (non-ghost) operation
    // ghost teardown
)
```

Inside the region, the invariant `P!<args!>()` is made available as a resource.
Before the region exits, `P!<args!>()` must be re-established (i.e., the
invariant body must be folded back).

**Example — try CAS with an integer invariant:**

```gobra
pred Own(x *int) { acc(x) }

requires Invariant(Own!<x!>)
decreases
func tryCAS(x *int) {
    var v int

    // Read the current value atomically.
    critical Own!<x!> (
        unfold Own!<x!>()     // open the invariant body
        v = Get(x)            // atomic operation
        fold Own!<x!>()       // re-establish the invariant
    )

    // Attempt to increment.
    critical Own!<x!> (
        unfold Own!<x!>()
        b = CAS(x, v, v+1)
        fold Own!<x!>()
    )
}
```

#### Rules inside a critical region

| What is allowed | Example |
|---|---|
| Arbitrary ghost code | `unfold`, `fold`, `assert`, ghost function calls |
| Exactly one non-ghost atomic call | `v = Get(x)`, `CAS(x, o, n)` |
| Interface method calls (see note below) | `i.M()` where `M` is `atomic` |

| What is forbidden | Reason |
|---|---|
| More than one atomic non-ghost call | Would allow two distinct linearization points |
| Non-atomic non-ghost operations (`*x += 1`) | Not linearizable |
| Atomic arguments that themselves read shared state (`CAS(x, *x, *x+1)`) | Arguments are evaluated before the atomic step; reading `*x` is not atomic |
| Re-opening an already-open invariant | Prevents re-entrance cycles |
| Calling `opensInvariants` ghost functions | Would allow nested opening in ghost context (see below) |

**Argument restrictions.** The arguments passed to the atomic call inside a
critical region must be of a restricted form: they may be local variables,
constants, and addresses of local variables. In particular, they may not involve
reads through pointers (such as `*x`) because such reads are not themselves
atomic and would therefore observe a pre-atomic state.

**Interface method calls in critical regions.** Calling an atomic interface
method `i.M()` inside a critical region is permitted even though, at the machine
level, it involves a vtable dispatch that is technically not a single instruction.
The call is safe because the vtable lookup is *transparent*: no other thread can
observe whether the lookup has happened yet. This holds because:

- If `i` is in an exclusive memory location, no other thread can change it
  between the dispatch and the actual call.
- If `i` is in a shared memory location, obtaining read permission to `i`
  (required for the dispatch) is sufficient. Regular (non-atomic) writes to
  interface variables are not atomic and therefore not permitted in critical
  regions, and the `sync/atomic` package does not offer atomic writes to
  interface-typed variables. Therefore no other thread can change `i` in an
  atomic step between dispatch and call.

The verifier treats such a call as if the dispatch happened atomically together
with the call body.

#### Invariants around loops

Gobra tracks which invariants are open or closed across loop iterations. If a
critical region closes an invariant before the loop body ends, the invariant
will be treated as closed at the top of the next iteration.

```gobra
requires Invariant(Own!<x!>)
func testLoops(x *int) {
    invariant Invariant(Own!<x!>)     // loop invariant: token persists
    for getRandomBool() {
        critical Own!<x!> (
            unfold Own!<x!>()
            assert acc(x)
            fold Own!<x!>()
        )
    }
}
```

### The `opensInvariants` Annotation

Ghost functions normally cannot contain critical regions. This restriction exists
because allowing ghost functions to open invariants would complicate re-entrance
checking: a ghost function with a critical region might be called from inside a
critical region of the same invariant, leading to a re-entrance violation that is
hard to detect statically.

The annotation `opensInvariants` explicitly opts a ghost function into invariant
opening:

```gobra
ghost
opensInvariants
decreases
func ghostHelper()
```

A ghost function annotated with `opensInvariants` may contain critical regions.
However, it may not be called from inside a critical region (to preserve the
"at most one open invariant at a time" guarantee), and any ghost function that
calls it must itself be annotated with `opensInvariants`.

```gobra
ghost
decreases
func fail() {
    ghostHelper()   // type error: caller must also be opensInvariants
}
```

Only ghost functions may be annotated with `opensInvariants`; non-ghost functions
never need it because they can use critical regions directly.

## Concurrency Abstraction Levels

The `atomic` annotation is relative to a concurrency abstraction level: a
method appears atomic *with respect to* the set of invariants that the caller
can observe. Concretely, the methods that are considered atomic at a given level
are exactly those marked `atomic` in the Gobra specification.

This means that a function can implement a higher-level atomic operation out of
lower-level atomic primitives (such as `CAS`) by choosing the right invariant
structure. The invariant encapsulates the implementation detail; callers see only
the atomic specification.

This design implicitly forms a *level hierarchy*:

- **Level 0** — hardware atomics and built-in atomic primitives.
- **Level n** — operations that are atomic with respect to invariants established
  from level-(n-1) operations.

The `EstablishInvariant` / critical-region mechanism is the bridge between
levels: establishing an invariant promotes state from one level to the next.

A soundness argument must account for the fact that the set of invariants in
scope is fixed at verification time. The assumption is that the implementation
of an abstract `atomic` method (which is not verified by Gobra) genuinely
provides atomicity at the level implied by its contract. This is an unverified
assumption — Gobra trusts the `atomic` annotation on abstract methods in the
same way it trusts `trusted` annotations. The programmer is responsible for
ensuring that the underlying implementation (e.g., a `sync/atomic` call) is
genuinely atomic at the intended level.

## Error Catalogue

| Error | Cause |
|---|---|
| `is_invariant_failed` | Entering a critical region without proof that the predicate is an established invariant |
| `invariant_not_restored` | Exiting a critical region without re-establishing the invariant |
| `invariant_already_open` | Attempting to open an invariant that is already open (re-entrance) |
| `assert_error` | A proof obligation inside a critical region does not hold |
| `type_error` (atomic restrictions) | More than one atomic call, non-atomic call, or invalid argument form inside a critical region |

## Restrictions Summary

| Feature | Restriction | Rationale |
|---|---|---|
| `atomic` | Only abstract (body-less) functions | Gobra cannot verify atomicity of concrete code |
| `atomic` | Must have `decreases` | Atomic steps must terminate |
| `atomic` | Not allowed on ghost functions | No run-time linearization point for ghost code |
| Critical region | Exactly one non-ghost atomic call | More than one would introduce two linearization points |
| Critical region | No non-atomic non-ghost calls | Non-atomic calls are not linearizable |
| Critical region | Arguments must be non-dereferencing | Argument evaluation happens outside the atomic step |
| Critical region | Cannot re-open an open invariant | Prevents re-entrance |
| Critical region | Cannot call `opensInvariants` functions | Prevents nested invariant opening in ghost context |
| `opensInvariants` | Only ghost functions | Non-ghost functions use critical regions directly |
| `opensInvariants` | Callers must also declare `opensInvariants` | Propagates the opening requirement up the call chain |
| `opensInvariants` | Functions cannot be called from critical regions | Prevents nested opening |

## Complete Example

The following example shows a spinlock-style increment using `CAS` and an
invariant.

```gobra
package spinlock

// Low-level atomic primitives (trusted / from runtime).
preserves acc(x)
ensures   b ==> *x == newv && old(*x) == oldv
ensures   !b ==> *x == old(*x) && old(*x) != oldv
decreases
atomic func CAS(x *int, oldv int, newv int) (b bool)

preserves acc(x)
decreases
atomic func Get(x *int) int

// Own encapsulates exclusive access to an integer.
pred Own(x *int) { acc(x) }

// increment atomically increments *x.
// It requires the invariant token so it can open the critical region.
requires Invariant(Own!<x!>)
func increment(x *int) {
    var swapped bool
    invariant Invariant(Own!<x!>)
    for !swapped {
        var v int
        critical Own!<x!> (
            unfold Own!<x!>()
            v = Get(x)
            fold Own!<x!>()
        )

        critical Own!<x!> (
            unfold Own!<x!>()
            swapped = CAS(x, v, v+1)
            fold Own!<x!>()
        )
    }
}

// main shows how to set up the invariant before launching goroutines.
func main() {
    x@ := 0
    fold Own!<&x!>()
    EstablishInvariant(Own!<&x!>)
    // Now Invariant(Own!<&x!>) can be shared with goroutines.
    increment(&x)
}
```

## Relationship to the Gobra Built-in `PredTrue`

The built-in predicate `PredTrue` (always true) can be used as a trivial
invariant when no shared state needs protection — e.g., to use a critical region
purely for its synchronisation effect on the verifier. It is referenced as
`PredTrue!<!>` (an FPredicate with no arguments).

This PR also fixes a pre-existing issue where users were required to write
`PredTrue!<!>()` (with the explicit instantiation brackets) in certain positions
where a plain `PredTrue()` should have been accepted. The fix applies to all
`BuiltInPredicate` instances.

## Future Work

- **Relaxing the one-atomic-call restriction.** The current design allows at most
  one non-ghost atomic call per critical region. A future extension could support
  multiple calls if the verifier can prove that they compose into a single logical
  step (e.g., via prophecy variables or helping).
- **Revoking invariants.** Allowing invariants to be un-established would require
  a more expressive permission model but would enable patterns such as
  object deallocation.
- **Concrete atomic implementations.** Currently the verifier trusts the `atomic`
  annotation on abstract functions. A future extension could verify that a
  concrete implementation genuinely linearizes correctly against its specification.
