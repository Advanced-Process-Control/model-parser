# model-parser

**Convert process-model definitions to and from a canonical intermediate representation (IR).**

`model-parser` owns the *model scaffold* contract for the Advanced Process Control
toolchain: it parses an authoring format (today: ExprTk-style INI) into a
normalized **canonical IR** (JSON), validates it, and lowers it to target views —
starting with generated **ModelingToolkit v11** Julia.

```text
authoring (ExprTk INI)  --parse-->  AST  --normalize-->  canonical IR (JSON)
                                                          |
                                          emit julia  --> ModelingToolkit .jl
```

## Where to read next

- **[Product specification](design/model-parser.md)** — authoritative scope, CLI, and behaviour.
- **[IR specification](design/ir-specification.md)** — IR shape and expression language.
- **[Decision log](decisions/index.md)** — ADRs for major design choices.
- **[PyPI package `apc-model-parser`](https://pypi.org/project/apc-model-parser/)** — installable CLI (`model-parser`).

## Install (uv)

```bash
uv tool install apc-model-parser
model-parser --help
```

For development, clone the repository and use `uv sync --all-groups` (see
[CI/CD and releases](deployment/ci-cd.md)).
