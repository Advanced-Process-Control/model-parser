# Examples

Small, copy-paste-friendly demonstrations of the `model-parser` pipeline. All
commands assume you have run `uv sync` in the repository root.

## Files

| Path | What it is |
|---|---|
| [`models/model_monod_simple.ini`](models/model_monod_simple.ini) | A 2-state Monod CSTR, no inputs. |
| [`models/model_thermal_tank.ini`](models/model_thermal_tank.ini) | A 2-state heated tank with 3 inputs. |
| [`run.sh`](run.sh) | Runs the full `parse → validate → emit` pipeline for both models. |

Generated artifacts are written to `outputs/` (git-ignored).

## The pipeline

```bash
# ExprTk INI  ->  canonical IR JSON
uv run model-parser parse examples/models/model_monod_simple.ini -o examples/outputs/monod.ir.json

# canonical IR  ->  ModelingToolkit (v11) Julia model
uv run model-parser emit julia examples/outputs/monod.ir.json -o examples/outputs/monod.jl

# validate against a backend profile
uv run model-parser validate examples/outputs/monod.ir.json --profile julia-analysis
uv run model-parser validate examples/models/model_thermal_tank.ini --profile realtime-cpp
```

Or run everything at once:

```bash
./examples/run.sh
```

## Notes

- `parse` warns that `[x0]` / `[u0]` initial values are **dropped** from the
  scaffold: initial values belong to a *scenario*, not the model IR.
- The generated `.jl` is a standalone artifact; load it with `include("monod.jl")`
  and call `build_monod_simple()`. Provide initial conditions and parameter
  overrides at `ODEProblem` construction time.
