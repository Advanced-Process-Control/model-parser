# ModelParserJL

Julia companion package for [`model-parser`](../../README.md). It loads a
**canonical model IR** (produced by the Python CLI) directly into a
[ModelingToolkit](https://github.com/SciML/ModelingToolkit.jl) `System`,
in memory, without a code-generation step.

This is the complementary path to `model-parser emit julia`:

| Path | Produces | Use when |
|---|---|---|
| `model-parser emit julia <ir>` (Python) | a re-runnable `.jl` **file** | you want a durable, diffable, version-controlled artifact (the default; see [ADR 0002](../../docs/decisions/0002-codegen-over-serialized-system.md)) |
| `ModelParserJL.build_system(ir)` (Julia) | an in-memory `System` | interactive / dynamic workflows; or as the conformance reference |

Both consume the **same** IR contract, so they stay semantically aligned.

## Usage

```julia
using Pkg; Pkg.activate("."); Pkg.instantiate()
using ModelParserJL

ir  = load_ir("monod.ir.json")     # parse the canonical IR JSON
sys = build_system(ir)             # compiled MTK System (v11)

using OrdinaryDiffEq
prob = ODEProblem(sys, [sys.x0 => 0.05, sys.x1 => 15.0], (0.0, 24.0))
sol  = solve(prob, Tsit5())
```

Initial values (`x0`, `u0`) and parameter overrides come from a **scenario** /
**parameter set**, not from the IR scaffold — pass them at `ODEProblem`
construction time.

## Requirements

- Julia ≥ 1.10
- `ModelingToolkit` v11, `JSON3`

Use Julia's package manager (`Pkg.add` / `Pkg.rm`) for dependencies.
