# model-parser design

## What it is

model-parser is the parser/IR/codegen hub for process-model scaffolds. It parses an authoring format (ExprTk-style INI from the MPC toolchain) into a canonical, backend-independent IR (JSON), validates it, and lowers it into generated views: a ModelingToolkit v11 model script, a plain Julia RHS, and a plain Python RHS. Published on PyPI as `apc-model-parser`; the command is `model-parser`.

It is not a simulator, identification tool, registry, deployment pipeline or UI. Parameter identification, scenario execution, result storage, linearization, MPC synthesis and deployment are sibling tools that consume the IR.

## Architecture

```text
authoring (.ini) --parse--> AST --normalize--> canonical IR (.ir.json)
                                                 |-- emit julia      -> MTK v11 builder .jl
                                                 |-- emit julia-rhs  -> f!/outputs! .jl
                                                 |-- emit python     -> f/outputs .py
                                                 '-- ModelParserJL.build_system (Julia, in memory)
```

Components (all under `src/model_parser/`):

- `frontends/expr_parser.py`: tokenizer and precedence-climbing parser for the ExprTk expression subset. Normalizes `pow` to `^`, `if` to `ifelse`, unary minus to `neg`.
- `frontends/exprtk_ini.py`: INI sections to IR. `[Dimensions]` is required. `[x0]`/`[u0]` are dropped with a WARN. Uses `SOURCE_DATE_EPOCH` for `provenance.created_at` when set.
- `ir/`: Pydantic models for the scaffold and the expression tree (`num`, `sym`, `call`). `ir/expr.py` is the only home of expression semantics. `schema.py` exports the JSON Schema to `schemas/canonical-ir.schema.json`.
- `validation/validators.py`: semantic checks (undeclared or duplicate symbols, missing equations, local ordering) and profile checks.
- `backends/`: one module per target. `julia_expr.py` holds Julia expression rendering shared by `julia_mtk.py` and `julia_rhs.py`; `python.py` is self-contained.
- `semantic_diff.py`: structural IR comparison and advisory model SemVer bump.
- `cli.py`, `io.py`: thin Typer CLI and file I/O. Everything else is pure.
- `julia/ModelParserJL`: Julia package that loads IR JSON into an in-memory MTK `System`; the dynamic path and the intended conformance reference.

Boundaries:

- Python and Julia never import each other; the IR JSON file is the only interface.
- `ir/`, `frontends/`, `backends/`, `validation/` do no I/O.
- The IR describes the scaffold only: variables, roles, units, parameter declarations with optional bootstrap defaults, locals, equations, profiles, provenance. Parameter sets and scenarios (initial values, inputs, horizons, solver settings) are sibling contracts.
- Identity is `provenance.content_hash`: sha256 over the canonical JSON of the IR body without `provenance`. Downstream artifacts reference a scaffold by hash, not path.
- Contract details: `docs/design/ir-specification.md` (IR), `docs/cli.md` (CLI and generated views), `docs/design/model-library-and-versioning.md` (hashes, SemVer, `diff`/`bump` policy, library layout).

## Key decisions

Language split

- Python owns CLI, parser, IR, schema, validation and codegen; Julia owns the in-memory `System` build. Each language is used where it is strong, and `parse`/`emit` need no Julia runtime.
- Both paths are optional and first-class: IR to `.jl` never needs Julia; the in-memory loader never needs the generated file.
- Python via uv with committed `uv.lock`; Julia via Pkg with `Manifest.toml` untracked. Keeps the library package resolvable on any Julia install.

IR and expressions

- Expressions are an explicit tagged tree, parsed once; no backend re-parses or rewrites strings. Precedence is resolved in one place and a new backend cannot reintroduce a parsing bug.
- `ifelse` is eager in every backend (Python emits an `_ifelse` helper, Julia uses symbolic `ifelse`). Matches ExprTk and MTK semantics; backends must not substitute short-circuit `if`.
- The operator/function set is explicit and extended deliberately. It is the expression sub-language contract.
- `ir_version` is SemVer: additive change is MINOR, breaking shape change is MAJOR and needs migration tooling. Regenerate and commit the JSON Schema on every shape change. The IR is a published contract consumed by `model-library`.
- Profiles (`julia-analysis` permissive, `realtime-cpp` restricted deterministic subset) are checked against the same IR. One model can be valid for analysis and rejected for a PLC target.

Storage and codegen

- Persist the IR plus generated `.jl`/`.py`, never a serialized MTK `System`. `System` internals change across MTK majors (v11 removed `defaults`, deprecated `@mtkmodel`) and a blob is opaque to non-Julia tools.
- Generated files are a pure function of the IR: regenerate, never hand-edit. One backend changes on MTK churn; stored IR is untouched.
- Compiled problems may be cached only as regenerable caches keyed on `content_hash`, MTK version and profile. They are never a source of truth.
- Output is byte-identical across runs and honours `SOURCE_DATE_EPOCH`. Lets `model-library` commit artifacts and fail CI on drift.

Julia MTK target

- Target MTK v11: `t_nounits`/`D_nounits`, `@parameters` with constant defaults, `@variables`, `System(eqs, t)`, `mtkcompile(sys; inputs = [...])`; never `@mtkmodel` or `structural_simplify`. Matches the ecosystem pin and avoids deprecated constructs.
- Numeric literals render as `Float64` (`2` becomes `2.0`). Predictable parameter typing under MTK parameter splitting.
- Bumping the targeted MTK major is a deliberate change with regenerated examples and updated idiom tests.

Numerical views

- `emit julia-rhs` emits `f_<slug>!(du, u, p, t[, inp])` and optional `outputs_<slug>!(y, u, p, t[, inp])`. For non-MTK workflows that need a plain in-place RHS from the same IR.
- `emit python` emits `f_<slug>(t, state, parameters[, inputs])` and optional `outputs_<slug>`, standard library only. SciPy argument order without a NumPy/SciPy runtime dependency.
- Packing follows IR declaration order for states, parameters, inputs and outputs; locals are evaluated sequentially in IR order. Parameter defaults are not applied inside the functions; callers pass numeric values. Execution and scenarios stay outside the parser.
- RHS generation lives here, not in consumers. Reimplementing equations downstream would duplicate expression semantics.

CLI

- Two core verbs: `parse` (authoring to IR, frontend picked by `--from`, default `exprtk-ini`) and `emit <target>` (a command group). A new frontend is a `--from` value and a new backend is a subcommand, both additive.
- Supporting commands: `validate`, `inspect`, `ast`, `schema`, `diff`, `bump`.
- Output defaults to stdout, `-o/--output` writes a file; kebab-case options; exit codes 0 ok, 1 validation errors, 2 usage or load failure; diagnostics use OK/WARN/ERROR. Composes in pipelines and CI.
- `diff`/`bump` live here as pure logic; lockfiles, layout, git tags and drift CI live in `model-library`. Keeps the parser small.
- `bump` is advisory and conservative: anything not clearly patch or minor is major. False compatibility is worse than an extra major.

Release

- Tag `vX.Y.Z` after bumping `pyproject.toml` and `src/model_parser/__init__.py`; `release.yml` builds, creates the GitHub Release with generated notes and publishes to PyPI via trusted publishing. No long-lived tokens.
- `CHANGELOG.md` at the repo root summarizes each version.

## Open

- `emit ini`: lower IR back to ExprTk INI with round-trip tests (structural IR equality where byte equality is impossible).
- `emit cpp` for the `realtime-cpp` profile: deterministic C++ for PLC/embedded targets, profile-checked operators only.
- Conformance fixtures: shared IR fixtures with golden `emit julia` output, run by Python and `ModelParserJL`; trajectory parity later (MTK vs `julia-rhs` vs Python).
- IR migrations: `model-parser migrate` tooling once a MAJOR `ir_version` bump is planned.
- Parameter-set contract: sibling JSON referencing a scaffold by `content_hash`; model-parser may only validate or inspect it.
- Optional inference of INI `[Dimensions]` from `dxN`/`yN`/`uN`, with ERROR on mismatch against explicit values.
- `diff`/`bump` as CI gates: `--fail-on <level>`, versioned `--json` schema, rules for float-literal and metadata-only churn.
- Schema hardening: richer units and bounds, role taxonomy.
