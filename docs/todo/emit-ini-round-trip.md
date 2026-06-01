# TODO: `emit ini` and round-trip

## Goal

Implement **`model-parser emit ini`** (or equivalent) so the canonical IR can be
lowered back to the ExprTk-style INI authoring shape, and add **round-trip
tests** (INI → IR → INI, and IR → INI → IR) with deterministic output.

## Why

- Reduces manual dual maintenance when a team wants both INI and IR in repo.
- Proves the IR is expressive enough for the legacy MPC authoring surface.
- Unlocks “regenerate INI from IR” in libraries without hand-editing two sources.

## Scope hints

- New backend module under `backends/`; no changes to existing backends except
  shared helpers if deduplication is obvious.
- Normalization rules (ordering, spacing, comments policy) must be documented;
  byte-identical round-trip may be impossible if INI discards information—define
  acceptable equivalence (e.g. structural IR equality).

## References

- [`docs/design/model-parser.md`](../design/model-parser.md) roadmap §3.
- [`docs/design/model-library-and-versioning.md`](../design/model-library-and-versioning.md).

## Acceptance sketch

- CLI: `model-parser emit ini <model.ir.json> [-o out.ini]`.
- Tests: at least one fixture from current `examples/models/*.ini`.
