# TODO: IR schema migrations (`ir_version`)

## Goal

When **`ir_version`** takes a **MAJOR** bump, ship **migration tooling** and
documentation so existing IR JSON and downstream repos can upgrade safely.

## Why

- The IR is a published contract; breaking shape changes without a path forward
  strand users and the model library lockfiles.
- [`docs/design/ir-specification.md`](../design/ir-specification.md) already
  requires migration notes + ADR on MAJOR changes—this task makes that concrete.

## Scope hints

- Command sketch: `model-parser migrate <from-ir.json> --to-ir-version X.Y.Z`
  (exact UX TBD via ADR).
- Pydantic / schema regen in the same change series as code
  (`schemas/canonical-ir.schema.json`).
- Optional: migration fixtures in `tests/` or `examples/`.

## References

- [`docs/design/ir-specification.md`](../design/ir-specification.md) §5.
- [`docs/decisions/index.md`](../decisions/index.md).

## Acceptance sketch

- ADR describing migration philosophy (lossless vs documented lossy transforms).
- At least one automated test for a trivial MAJOR migration path (can start with
  a no-op or rename field once a real bump is planned).
