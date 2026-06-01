# TODO: Optional inference of INI `[Dimensions]`

## Goal

Allow ExprTk INI models to omit or relax **`[Dimensions]`** when **`num_states`**
/ **`num_inputs`** / **`num_outputs`** can be **inferred** from `dx*`, `y*`,
and references to `u*` in expressions—while preserving a clear error surface for
ambiguous files.

## Why

- Reduces redundancy and copy-paste errors; dimensions must stay consistent with
  equations today by hand.
- Purely a **frontend** concern; IR shape unchanged.

## Scope hints

- Conservative inference: max index from `dxN`, `yN`, and `uN` symbol references.
- Ambiguity or mismatch vs explicit `[Dimensions]` → `ERROR` with actionable
  message (policy TBD in ADR or design doc update).

## References

- `src/model_parser/frontends/exprtk_ini.py`.
- [`docs/design/model-library-and-versioning.md`](../design/model-library-and-versioning.md) §7.

## Acceptance sketch

- Tests: models with inferred dimensions equivalent to current explicit examples.
- Doc update for INI grammar in frontend module docstring and design docs.
