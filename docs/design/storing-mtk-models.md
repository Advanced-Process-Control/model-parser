# Storing ModelingToolkit models

> "How do we store an MTK model for later use?" — short answer: **don't store the
> `System` object. Store the IR, and (re)generate the `.jl` from it.**

## 1. The temptation and why it fails

The obvious idea is to build an MTK `System` and serialize it (via Julia's
`Serialization`, `JLD2`, etc.) so it can be reloaded later. This is fragile:

- **The `System` type is an internal, evolving structure.** ModelingToolkit v11
  re-architected it for precompilation; `variable => value` mappings are now
  stored as `AbstractDict{SymbolicT, SymbolicT}` with `SymbolicUtils.Const`
  wrappers. A pickled object from one version may not deserialize correctly in
  the next.
- **Semantics moved underneath the object.** v11 **removed `defaults`**,
  replacing them with `initial_conditions` and `bindings`; v10 renamed
  `structural_simplify` → `mtkcompile` and changed callback/affect semantics;
  v9 changed parameter typing and splitting. A serialized object encodes
  decisions that later versions interpret differently.
- **`@mtkmodel` is deprecated** (moved to SciCompDSL.jl), so even a stored macro
  expansion is a moving target.
- **It is opaque.** A binary `System` blob is not diffable, not reviewable, and
  not consumable by C++ or any non-Julia tool.

In short: the `System` is a *compilation product*, not a storage format. Tying
long-term storage to one symbolic library's internal API is exactly the
"symbolic API churn" risk the ecosystem design warns about.

## 2. The chosen approach

A durable **canonical IR JSON** plus **one or more generated Julia views** from
the same IR:

1. **Canonical IR JSON** — the source of truth. Language-neutral, diffable,
   schema-validated, content-hashed. This is what we persist and version.
2. **Generated `.jl` scripts** — produced by `model-parser emit julia` (MTK
   `System` builder) and, when needed, `model-parser emit julia-rhs` (plain
   `f!` / `outputs!` for vector ODE workflows). Plain-text, re-runnable artifacts
   regenerated whenever the IR changes; never hand-edited.

```text
                 store / version
                 ┌──────────────┐
  authoring ──►  │ IR JSON      │  ──emit julia──►  MTK builder .jl ──►  System
   (.ini)        │ (.ir.json)   │  ──emit julia-rhs──►  f!/outputs! .jl
                 └──────────────┘
                        │
                        └────────  ModelParserJL.build_system(ir)  ──►  System
                                   (in-memory, no file)
```

The `System` itself lives only **in memory**, rebuilt on demand from a durable,
human-readable source. If MTK changes again, we update the *one* codegen
backend (and `ModelParserJL`) and regenerate — the stored IR is untouched.

## 3. Codegen vs in-memory loader

| | `emit julia` (Python codegen) | `ModelParserJL.build_system` (Julia) |
|---|---|---|
| Output | a `.jl` file | an in-memory `System` |
| Durable? | yes — commit it | no — rebuilt each run |
| Needs Julia to produce? | no | yes |
| Best for | reproducible artifacts, review, CI, handoff | interactive/dynamic work, conformance reference |

Both consume the same IR, so they agree by construction (and by conformance
tests). See [ADR 0002](../decisions/0002-codegen-over-serialized-system.md).

## 4. What about compiled problems and caches?

A *compiled* `ODEProblem` or generated function can be **cached** for speed, but
it is treated as a regenerable cache (machine-local, under a cache directory),
never as the source of truth. The cache key includes the IR `content_hash`, the
MTK version, and the profile, so a stale cache is detectable.

## 5. Where the numbers live

The generated `System` is a *scaffold*. Initial values and parameter overrides
are supplied at problem-construction time from a **scenario** / **parameter
set**, not baked into the stored model:

```julia
include("monod.jl")
sys = build_monod_simple()
prob = ODEProblem(sys, [sys.x0 => 0.05, sys.x1 => 15.0], (0.0, 24.0),
                  [sys.mu_max => 0.4])
```

This keeps the stored model reusable across experiments and keeps the IR a clean
scaffold contract.

## 6. Generated-code conventions (MTK v11)

The codegen targets v11 idioms so generated files stay valid as the prototype's
`ProcessModelingJL` does today:

- `using ModelingToolkit: t_nounits as t, D_nounits as D`;
- explicit `@variables` / `@parameters` (with constant defaults attached, which
  v11 translates into `initial_conditions`);
- `System(eqs, t)` then `mtkcompile(sys; inputs = [...])`;
- **no** `@mtkmodel`, **no** `structural_simplify`;
- `Float64` numeric literals for predictable parameter typing.

See [ADR 0004](../decisions/0004-target-mtk-v11-idioms.md).
