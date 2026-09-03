# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This package (`resalgebra`) is part of the `gobra-libs` project—a collection of reusable Gobra verification libraries. It provides a **verified model of ghost locations and relational algebras**, inspired by the Iris separation logic framework but implemented entirely in Gobra. All RA lemmas are proven within Gobra using pure functions rather than relying on axioms.

## Architecture

### Core Components

**RA Interface** (`ra.gobra`):
- Defines `RA` (Relational Algebra) interface with methods: `IsElem`, `IsValid`, `Core`, `Compose`
- All lemmas (`ComposeAssoc`, `ComposeComm`, `CoreId`, `CoreIdem`, `CoreMono`, `ValidOp`) are universally quantified
- Wrapper functions (e.g., `ComposeAssocQ`) lift instance-level lemmas to universally quantified facts

**Ghost Locations** (`loc.gobra`, `uniqueloc.gobra`):
- `GhostLocationW(l, ra, e, w)` - internal witness-based representation (Gobra cannot existentially quantify over resources)
- Witness-based operations (`loc.gobra`): `AllocW`, `GhostOp1W`, `GhostOp2W`, `GhostValidW`, `GhostUpdateW`; the `*WI` variants are the same operations without acquiring the global invariant
- `UniqueLoc` (`uniqueloc.gobra`) - public, opaque handle bundling a `LocName` and its `Witness` in two unexported fields; `GetLocName()` exposes the (stable) location name
- `GhostLocation(u, ra, e)` - public predicate for ghost state ownership, defined as `GhostLocationW(u.l, ra, e, u.w)`
- Public operations (`uniqueloc.gobra`): `Alloc`, `GhostOp1` (split), `GhostOp2` (merge), `GhostValid`, `GhostUpdate` - all proven wrappers around the witness-based operations, so the public API adds no assumptions
- `GlobalMem()` - package invariant ensuring consistency of all ghost locations

**RA Instantiations**:
- `auth.gobra` - Authorization RA (pairs of `IntWithTopBot` and `int`)
- `oneshot.gobra` - One-shot RA (states: Pending, Shot(n), Fail)

**Supporting Data Structures**:
- `cooliosetio.gobra` - Monotonic (append-only) set
- `cooliomapio.gobra` - Monotonic map
- `ras-map.gobra` - Map from `LocName` to `RA`

### Key Design Patterns

1. **Witness-based existential quantification**: Due to Gobra limitations, existential quantification uses explicit `Witness` values. The `W` suffix denotes witness-requiring variants (e.g., `GhostLocationW` vs `GhostLocation`). Rather than assuming intro/elim rules for the existential, the public API hides the witness inside the `UniqueLoc` newtype. Because splitting a resource produces new witnesses, a `UniqueLoc` identifies one *share* of a location: clients that must re-establish an invariant (e.g. a lock invariant) store the current share in a ghost field and parameterize the invariant by the stable `LocName`, as `oneshot_test.gobra` illustrates.

2. **Frame-preserving updates**: `IsFramePreservingUpdate(ra, e1, e2)` ensures updates preserve validity under arbitrary composition—central to the ghost state model.

3. **Package invariant**: `pkgInvariant GlobalMem()` declared at the top of `loc.gobra` ensures the global memory invariant is maintained.
