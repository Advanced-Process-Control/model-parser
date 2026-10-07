# CLI and generated views

## Commands

```text
model-parser parse   <authoring-file> [--from exprtk-ini] [-o out.ir.json]
model-parser emit julia      <model.ir.json>             [-o out.jl]
model-parser emit julia-rhs  <model.ir.json>             [-o out.jl]
model-parser emit python     <model.ir.json>             [-o out.py]
model-parser validate <model.ir.json | authoring-file> [--profile <name>]
model-parser inspect  <model.ir.json | authoring-file>
model-parser diff     <old.ir.json> <new.ir.json>         [--json]
model-parser bump     <old.ir.json> <new.ir.json>         [--json]
model-parser ast      <authoring-file>                      [-o out.json]
model-parser schema                                         [-o schema.json]
```

- `parse` turns an authoring file into canonical IR. The only frontend is `exprtk-ini`. `[x0]`/`[u0]` sections are dropped with a WARN because initial values are scenario data.
- `emit <target>` lowers IR into a view: `julia` (ModelingToolkit v11 builder), `julia-rhs` (plain `f!`/`outputs!`), `python` (plain RHS and output functions).
- `validate` accepts IR or an authoring file (parsed on the fly) and an optional profile.
- `inspect` prints a summary, `ast` exports the debug parse tree, `schema` exports the IR JSON Schema.
- `diff` lists semantic changes between two IR files; `bump` suggests a model SemVer bump (see [Model library & versioning](design/model-library-and-versioning.md)).

Output goes to stdout unless `-o` is given. Exit codes: `0` success, `1` validation errors, `2` usage or load failure. Diagnostics use `OK` / `WARN` / `ERROR`.

Set `SOURCE_DATE_EPOCH` to make `provenance.created_at`, and therefore committed IR files, byte-stable.

## Typical session

```bash
model-parser parse  examples/models/model_monod_simple.ini -o monod.ir.json
model-parser validate monod.ir.json --profile julia-analysis
model-parser emit julia     monod.ir.json -o monod.jl
model-parser emit julia-rhs monod.ir.json -o monod_rhs.jl
model-parser emit python    monod.ir.json -o monod.py
```

## Profiles

- `julia-analysis`: permissive, the full IR is allowed.
- `realtime-cpp`: restricted deterministic operator/function subset for PLC targets. Validation only; there is no C++ backend yet.

## Generated views

All views are generated from the IR and must not be edited by hand; regenerate instead.

`emit julia` writes a `build_<model>()` function that returns a compiled MTK `System`. It uses `System(eqs, t)` and `mtkcompile`, never `@mtkmodel` or `structural_simplify`, and renders numeric literals as `Float64`. Initial values and parameter overrides are supplied when building the problem:

```julia
include("monod.jl")
sys = build_monod_simple()
prob = ODEProblem(sys, [sys.x0 => 0.05, sys.x1 => 15.0], (0.0, 24.0),
                  [sys.mu_max => 0.4])
```

`emit julia-rhs` writes `f_<model>!(du, u, p, t)` (or `f_<model>!(du, u, p, t, inp)` when the model has inputs) and, when the IR has output equations, `outputs_<model>!(y, u, p, t[, inp])`.

`emit python` writes `f_<model>(t, state, parameters[, inputs])`, which returns the derivative list in SciPy argument order, and `outputs_<model>` with the same arguments when output equations exist. Generated modules use only the standard library.

Packing for both numerical views: states, parameters, inputs and outputs follow their IR declaration order. Parameter defaults are not applied; callers pass numeric values. Conditionals are eager: both branches are evaluated before selection.
