# ADR 0002 — Generate Julia code; do not serialize the MTK `System`

**Status:** accepted · 2026-06-01

## Context

We need a way to "store an MTK model for later use." The direct option is to
build a `System` and serialize the object (`Serialization`, `JLD2`). But the
`System` is a compilation product of a fast-moving library: ModelingToolkit v11
re-architected it for precompilation (symbolic values wrapped as
`SymbolicUtils.Const`), **removed `defaults`** in favor of `initial_conditions`
and `bindings`, renamed `structural_simplify` → `mtkcompile` (v10), changed
parameter typing/splitting (v9), and **deprecated `@mtkmodel`**. A serialized
object encodes version-specific semantics and is opaque to non-Julia tools.

## Decision

Persist the model as **(1) the canonical IR JSON** (source of truth) and
**(2) a generated `.jl` script** emitted by `model-parser emit julia`. The
`System` exists only in memory, rebuilt on demand:

- from the generated `.jl` (`include` + `build_<name>()`), or
- directly from the IR via `ModelParserJL.build_system` for dynamic use.

Compiled problems/functions may be **cached** (keyed by IR `content_hash` + MTK
version + profile) but are never the source of truth.

## Consequences

- + Durable, diffable, reviewable artifacts; survive MTK upgrades by
  regeneration.
- + The stored form is language-neutral (IR) plus human-readable (generated
  Julia).
- + One place to update on symbolic-API churn: the codegen backend (+ the Julia
  loader), not every stored model.
- − A rebuild/regeneration step is required before use (acceptable: fast and
  cacheable).
- − Two representations to keep consistent (IR and generated `.jl`); mitigated by
  treating `.jl` as a pure function of the IR and regenerating, never editing.

## Alternatives considered

- *Serialize the `System` (JLD2/Serialization).* Rejected: brittle across MTK
  versions, opaque, Julia-only.
- *Store an FMU.* Reasonable as a *derived artifact* later, but it is a heavy,
  backend-specific export — not the primary storage contract for a scaffold.
- *Store only the IR and always use the in-memory loader.* Viable, but the
  generated `.jl` adds a reviewable, runnable artifact and removes the Julia
  runtime requirement from the producing step.

## References

- ModelingToolkit v11 release notes (System internals, `defaults` removal,
  `@mtkmodel` deprecation): <https://github.com/SciML/ModelingToolkit.jl/blob/master/NEWS.md>
- [`docs/design/storing-mtk-models.md`](../design/storing-mtk-models.md)
- Org architecture: analysis-time vs run-time separation
