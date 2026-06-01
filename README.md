# model-parser

**Convert process-model definitions to and from a canonical intermediate
representation (IR).**

`model-parser` is the Advanced Process Control toolbox component that owns the
*model scaffold* contract and the transformations around it. It parses an
authoring format (today: the ExprTk-style INI used by the MPC / simulation
toolchain) into a normalized, backend-independent **canonical IR**, and lowers
that IR into target views — starting with a generated **ModelingToolkit (Julia)**
model script.

```text
authoring (ExprTk INI)  --parse-->  AST  --normalize-->  canonical IR (JSON)
                                                          |
                                          emit julia  --> ModelingToolkit .jl
                                          emit cpp    --> (planned) realtime C++
```

The IR is the single semantic contract. Adding a backend means writing one
`lower` + one `export`, not an N×N mesh of view-to-view translators. See
[`docs/design/model-parser.md`](docs/design/model-parser.md) for the
authoritative product specification and
[`docs/decisions/`](docs/decisions/) for the design decision records.

## Why two languages?

| Concern | Home | Why |
|---|---|---|
| CLI, AST, IR, JSON Schema, validators, **codegen** | **Python** (this package) | Parsing & orchestration strength; no symbolic runtime needed to emit code. |
| IR → MTK `System`, simulation, analysis, conformance | **Julia** ([`julia/ModelParserJL`](julia/ModelParserJL/)) | Natural fit for ModelingToolkit; reference for parity tests. |

The Python CLI builds and validates the IR and **generates** Julia code; the
Julia package can additionally load an IR directly into an MTK `System` for
in-memory, dynamic workflows. Both consume the *same* IR. See
[ADR 0001](docs/decisions/0001-python-cli-with-julia-backend.md).

## Install

### CLI from PyPI (end users)

The package on PyPI is **`apc-model-parser`**; the installed command is **`model-parser`**.

```bash
pipx install apc-model-parser
# or: uv tool install apc-model-parser
model-parser --help
```

Use **`pipx`** or **`uv tool`** when you only need the CLI in an isolated environment.

### From source (development)

This repository uses **[uv](https://docs.astral.sh/uv/)** for environments and tasks.

```bash
uv sync --all-groups    # include dev tools (ruff, pytest, mkdocs)
uv run model-parser --help
```

## CLI

```bash
# 1. ExprTk INI  ->  canonical IR JSON
uv run model-parser parse examples/models/model_monod_simple.ini -o monod.ir.json

# 2. canonical IR  ->  ModelingToolkit (v11) Julia model
uv run model-parser emit julia monod.ir.json -o monod.jl

# Supporting commands
uv run model-parser validate monod.ir.json --profile julia-analysis
uv run model-parser inspect  monod.ir.json
uv run model-parser diff     monod.ir.json other.ir.json   # semantic IR diff
uv run model-parser bump     monod.ir.json other.ir.json   # suggested SemVer bump
uv run model-parser ast      examples/models/model_monod_simple.ini   # debug tree
uv run model-parser schema   -o schemas/canonical-ir.schema.json      # export schema
```

`parse` accepts `--from exprtk-ini` (default). `validate` accepts either an IR
`.json` file or an INI file (parsed on the fly). Exit codes: `0` success,
`1` validation errors, `2` usage / load failure.

## How "stored MTK models" work

The persisted, version-controlled form of a model is the **IR JSON** plus the
**generated `.jl` script** — *not* a serialized `System` object. ModelingToolkit
v11 changed `System` internals significantly (precompilation, removal of
`defaults`, deprecation of `@mtkmodel`), so serializing the live object is
brittle across versions. Regenerating from the IR is the durable path. See
[ADR 0002](docs/decisions/0002-codegen-over-serialized-system.md) and
[`docs/design/storing-mtk-models.md`](docs/design/storing-mtk-models.md).

## Development

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run mkdocs build --strict   # same as CI
```

Documentation site (after [Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow) is set to GitHub Actions):
[https://advanced-process-control.github.io/model-parser/](https://advanced-process-control.github.io/model-parser/)

## Scope

**In scope:** authoring-format parsing, the canonical IR data model + JSON
Schema, semantic & profile validation, IR↔backend lowering/codegen.

**Out of scope:** parameter identification, scenario execution, simulation
result storage, controller synthesis, deployment. Those are sibling tools that
*consume* the IR. The parser stays small (see
[`AGENTS.md`](AGENTS.md) scope guardrails).
