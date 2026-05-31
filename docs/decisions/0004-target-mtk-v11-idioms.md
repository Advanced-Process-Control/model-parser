# ADR 0004 — Generated Julia targets ModelingToolkit v11 idioms

**Status:** accepted · 2026-06-01

## Context

ModelingToolkit changes its public surface across major versions. The codegen
backend must emit code that is valid and idiomatic for the version the ecosystem
runs (`ProcessModelingJL` pins `ModelingToolkit = "11.18.0"`). Several v9–v11
changes directly affect generated code:

- `structural_simplify` → **`mtkcompile`** (v10);
- `@mtkmodel` **deprecated** and moved to SciCompDSL.jl (v11);
- **`defaults` removed**, replaced by `initial_conditions` / `bindings` (v11);
- a single unified **`System`** type with `System(eqs, t[, vars, pars])` (v10);
- parameter typing matters under parameter splitting (v9): a literal `2` and
  `2.0` are not interchangeable.

## Decision

The Julia codegen backend (`backends/julia_mtk.py`) targets **MTK v11 idioms**:

- import time as `using ModelingToolkit: t_nounits as t, D_nounits as D`;
- declare `@parameters name = value …` (constant defaults; v11 translates these
  into `initial_conditions`) and `@variables name(t) …`;
- build with `System(eqs, t)` then `mtkcompile(sys; inputs = [...])`;
- **never** emit `@mtkmodel` or `structural_simplify`;
- render numeric literals as `Float64` (`2` → `2.0`) for predictable parameter
  typing;
- use symbolic `ifelse` (eager) for conditionals, matching the IR semantics.

The targeted MTK major version is recorded; bumping it is a deliberate change
with regenerated examples and (later) conformance runs.

## Consequences

- + Generated models load and `mtkcompile` cleanly on the pinned MTK version, the
  same way the hand-written prototype models do.
- + Decoupling "model meaning" (IR) from "MTK API version" (codegen) means an MTK
  upgrade is a single-backend change plus regeneration.
- − The backend is version-aware and must be revisited on MTK majors. This is
  expected and is exactly why the IR — not the generated code — is the source of
  truth (ADR 0002).
- − Tests assert on emitted idioms (e.g. absence of `@mtkmodel`), so an
  intentional idiom change updates tests in the same series.

## Alternatives considered

- *Target an older MTK API for stability.* Rejected: the ecosystem already runs
  v11 and benefits from its faster TTFX; emitting deprecated constructs is a
  future liability.
- *Emit version-agnostic code via a compatibility shim.* Rejected as premature
  complexity; a single targeted version with regeneration is simpler and matches
  the codegen-over-serialization stance.

## References

- ModelingToolkit v9/v10/v11 release notes:
  <https://github.com/SciML/ModelingToolkit.jl/blob/master/NEWS.md>
- `apcplants/ProcessModelingJL` (working v11 patterns; `Project.toml` compat)
- [`docs/design/storing-mtk-models.md`](../design/storing-mtk-models.md) §6
