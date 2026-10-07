# model-parser

**Convert process-model definitions to and from a canonical intermediate representation (IR).**

`model-parser` owns the *model scaffold* contract for the Advanced Process Control
toolchain: it parses an authoring format (today: ExprTk-style INI) into a
normalized **canonical IR** (JSON), validates it, and lowers it to target views —
including generated **ModelingToolkit v11**, Julia RHS, and Python functions.

```text
authoring (ExprTk INI)  --parse-->  AST  --normalize-->  canonical IR (JSON)
                                                          |
                                          emit julia      --> ModelingToolkit .jl
                                          emit julia-rhs  --> numerical f!/outputs! .jl
                                          emit python     --> numerical functions .py
```

## Where to read next

- **[CLI and generated views](cli.md)**: commands, profiles, and the contract of each emitted view.
- **[IR specification](design/ir-specification.md)**: IR shape and expression language.
- **[Model library & versioning](design/model-library-and-versioning.md)**: hashes, SemVer, `diff`/`bump`, sibling `model-library`.
- **[PyPI package `apc-model-parser`](https://pypi.org/project/apc-model-parser/)**: installable CLI (`model-parser`).

Architecture and design decisions live in `DESIGN.md` at the repository root.

## Install from PyPI

The distribution name is **`apc-model-parser`**; the CLI entry point is **`model-parser`**.

```bash
pipx install apc-model-parser
# or:
uv tool install apc-model-parser

model-parser --help
```

**`pipx`** and **`uv tool`** both install the tool into an isolated environment and put `model-parser` on your `PATH`.

For **development** from a clone, use **`uv sync --all-groups`** (see [CI/CD and releases](deployment/ci-cd.md)).
