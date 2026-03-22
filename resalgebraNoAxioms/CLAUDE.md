# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This package (`resalgebraNoAxioms`) is part of the `gobra-libs` project—a collection of reusable Gobra verification libraries. It provides a **verified model of ghost locations and relational algebras without axioms**, inspired by the Iris separation logic framework but implemented entirely in Gobra.

Key distinction from the `resalgebra` sibling package: all lemmas are proven within Gobra using pure functions rather than relying on axioms (hence "NoAxioms").

## Verification Commands

The project uses Gobra with the Viper/SILICON backend. Verification runs via GitHub Actions on push to `main` and on PRs.

**CI configuration** (from `.github/workflows/gobra.yml`):
- Backend: SILICON
- Recursive verification enabled
- Timeout: 5 minutes per package
- Key flags: `checkConsistency: 1`, `assumeInjectivityOnInhale: 0`, `parallelizeBranches: 0`

To verify locally, use the Gobra verifier with equivalent settings.

## Architecture

### Core Components

**RA Interface** (`ra.gobra`):
- Defines `RA` (Relational Algebra) interface with methods: `IsElem`, `IsValid`, `Core`, `Compose`
- All lemmas (`ComposeAssoc`, `ComposeComm`, `CoreId`, `CoreIdem`, `CoreMono`, `ValidOp`) are universally quantified
- Wrapper functions (e.g., `ComposeAssocQ`) lift instance-level lemmas to universally quantified facts

**Ghost Locations** (`loc.gobra`):
- `GhostLocation(l, ra, e)` - public predicate for ghost state ownership
- `GhostLocationW(l, ra, e, w)` - internal witness-based representation (Gobra cannot existentially quantify over resources)
- `IntroExists`/`ElimExists` - trusted functions bridging the two representations
- Operations: `Alloc`, `GhostOp1` (split), `GhostOp2` (merge), `GhostValid`, `GhostUpdate`
- `GlobalMem()` - package invariant ensuring consistency of all ghost locations

**RA Instantiations**:
- `auth.gobra` - Authorization RA (pairs of `IntWithTopBot` and `int`)
- `oneshot.gobra` - One-shot RA (states: Pending, Shot(n), Fail)

**Supporting Data Structures**:
- `cooliosetio.gobra` - Monotonic (append-only) set
- `cooliomapio.gobra` - Monotonic map
- `ras-map.gobra` - Map from `LocName` to `RA`

### Key Design Patterns

1. **Witness-based existential quantification**: Due to Gobra limitations, existential quantification uses explicit `Witness` values. The `W` suffix denotes witness-requiring variants (e.g., `GhostLocationW` vs `GhostLocation`).

2. **Frame-preserving updates**: `IsFramePreservingUpdate(ra, e1, e2)` ensures updates preserve validity under arbitrary composition—central to the ghost state model.

3. **Package invariant**: `pkgInvariant GlobalMem()` declared at the top of `loc.gobra` ensures the global memory invariant is maintained.

4. **Layered API**: Functions come in pairs—`*WI` functions require `GlobalMem()` explicitly, `*W` functions inhale/exhale the invariant internally.

## Gobra-Specific Notes

- Files begin with `// +gobra` to mark them for Gobra verification
- `ghost` keyword marks verification-only (non-executable) code
- `trusted` functions are assumed correct without proof
- `opaque` functions hide their body from the verifier unless explicitly revealed
- Predicates (`pred`) define separation logic assertions
- `decreases` clauses prove termination
