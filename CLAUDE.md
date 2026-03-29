# CLAUDE.md

## Project Overview

`gobra-libs` is a verification library for [Gobra](https://github.com/viperproject/gobra), a verifier for Go programs built on top of Viper. It provides reusable definitions and lemmas for formal verification projects.

## Repository Structure

Each top-level directory is a Gobra package:

| Package | Purpose |
|---------|---------|
| `sets/` | Set operations and lemmas |
| `seqs/` | Sequence/list operations and lemmas |
| `dicts/` | Mathematical map definitions and lemmas |
| `gomap/` | Go map verification utilities |
| `bytes/` | Byte operations |
| `byteslice/` | ByteSlice helper functions |
| `runeslice/` | Rune slice helper functions |
| `math/` | Natural numbers and math utilities |
| `util/` | General utility functions |
| `resalgebra/` | Resource algebra framework (with axioms) (deprecated) |
| `resalgebraNoAxioms/` | Resource algebra framework (without axioms) |
| `refinement/` | Refinement type support (deprecated) |
| `refinementguard/` | Refinement with guards and LIIs |
| `genericmonomap/` | Generic monotonic map |
| `genericmonoset/` | Generic monotonic set |
| `evaluation/` | Performance evaluation scripts (Python) |

## Source Files

All source files use the `.gobra` extension and must begin with:
```
//+gobra
```

Test files follow the naming convention `*_test.gobra`.

## Verification

This is a pure verification library — there is no compiled binary. Correctness is established by running the Gobra verifier over all packages.

### CI

Verification runs automatically via GitHub Actions (`.github/workflows/gobra.yml`) on every push to `main` and on all pull requests. Key settings:

- Backend: Silicon (Z3-based SMT solver)
- `checkConsistency`: enabled
- `assumeInjectivityOnInhale`: disabled
- `parallelizeBranches`: disabled
- `mceMode`: on (default setting)
- Timeout: 5 minutes per run

### Running Locally

To verify locally, use the [gobra-action](https://github.com/viperproject/gobra-action) or run Gobra directly:

```bash
java -Xss1g -Xmx4g -XX:-UseContainerSupport -Dcom.sun.management.jmxremote=false -jar /gobra/gobra.jar --recursive --projectLocation gobra-libs --includePaths . \
  --viperBackend SILICON --checkConsistency
```

Refer to the Gobra documentation for installation and usage details.

## Contributing

- All packages must verify successfully with Gobra before merging.
- Contributed definitions should be generally reusable across verification projects.
- Follow the existing file header conventions (license comment + `//+gobra`).
- Keep packages focused; add new packages for unrelated functionality rather than expanding existing ones.

## Gobra-Specific Notes

- `ghost` keyword marks verification-only (non-executable) code
- `trusted` functions are assumed correct without proof
- `opaque` functions hide their body from the verifier unless explicitly revealed
- Predicates (`pred`) define separation logic assertions
