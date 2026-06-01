# TODO: Harden `diff` / `bump` for library CI

## Goal

Evolve **`model-parser diff`** and **`model-parser bump`** from advisory output
into optional **CI gates**: stricter classification, exit codes, and documented
policy for how `model-library` (and others) should interpret results.

## Why

- Libraries want “fail if this would be a MAJOR bump without version bump” or
  similar policies.
- Edge cases (e.g. floating-point literal normalization, metadata-only churn)
  need explicit rules.

## Scope hints

- Flags sketch: `--fail-on major`, `--json` stable schema versioning.
- Extend `src/model_parser/semantic_diff.py` with tests for each policy branch.
- Cross-link from [`docs/design/model-library-and-versioning.md`](../design/model-library-and-versioning.md).

## References

- `src/model_parser/cli.py` (`diff`, `bump`).
- `tests/test_semantic_diff.py`.

## Acceptance sketch

- Documented policy table + tests for CI-oriented flags.
- Example GitHub Actions snippet in `model-library` or parser deployment docs.
