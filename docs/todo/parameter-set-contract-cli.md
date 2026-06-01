# TODO: Parameter set contract and optional CLI

## Goal

Define and (where appropriate) implement the **sibling JSON contract** for
**parameter sets**: numeric values fitted or chosen for a scaffold, referenced
by **`content_hash`** (and/or model id + lockfile policy), **not** embedded as
the sole truth in the INI `[Parameters]` section.

## Why

- Aligns repositories with the scaffold vs parameter set split already stated in
  product docs and org contracts.
- Enables multiple value sets per scaffold (calibration, deployment, what-if)
  without duplicating equations.

## Scope hints

- **Contract first** (schema, examples, ADR); `model-parser` might only validate
  or `inspect` parameter sets, or a separate small tool might own the file—keep
  scope guardrails in mind (repository root `AGENTS.md`).
- INI frontend might grow optional “declarations only” mode later; not required
  for the first parameter-set slice.

## References

- [`docs/design/model-parser.md`](../design/model-parser.md) §4.
- [`docs/design/model-library-and-versioning.md`](../design/model-library-and-versioning.md) §7.

## Acceptance sketch

- Published JSON Schema (or org repo location) + example files.
- Clear story for how `model-library` (or customers) pins `content_hash` + set id.
