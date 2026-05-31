# Coding agent guidelines for model-parser

This file defines how AI coding agents (e.g. Cursor, Copilot) and human
contributors collaborate on this repository. It is **public**: describe
behaviour only in terms of this project and its published design — avoid
internal codenames or unrelated repositories.

**Authoritative product specification:**
[`docs/design/model-parser.md`](docs/design/model-parser.md). When CLI
semantics, the IR shape, scope, or roadmap change, update that document (and the
relevant `docs/decisions/NNNN-*.md` ADR) in the same change series as the code.

## What this repository is

`model-parser` converts process-model definitions **to and from a canonical
intermediate representation (IR)**. It owns the model-*scaffold* contract: the
parser, AST, normalizer, IR data model + JSON Schema, validators, and the
IR→backend lowerings (codegen). It is one tool in the Advanced Process Control
ecosystem and must remain usable **standalone**.

```text
authoring (ExprTk INI)  --parse-->  AST  --normalize-->  canonical IR (JSON)
                                                          |
                                          emit julia  --> ModelingToolkit .jl
                                          emit cpp    --> (planned) realtime C++
```

## Language

- **All content in English:** code, comments, docstrings, commit messages,
  user-facing CLI strings, `docs/chatlogs/` entries, and Markdown under `docs/`.
- Keep domain vocabulary consistent with the org glossary and design docs:
  *scaffold*, *parameter set*, *scenario*, *AST*, *canonical IR*, *profile*,
  *lower*, *export*, *conformance*, *provenance*.

## Two languages, one contract

| Concern | Home |
|---|---|
| CLI, AST, IR data model, JSON Schema, validators, **codegen** | **Python** (`src/model_parser/`) |
| IR → ModelingToolkit `System`, in-memory build, conformance reference | **Julia** (`julia/ModelParserJL/`) |

Both consume the **same** IR JSON. Do not re-implement expression semantics in
more than one place without IR-level tests. See
[`docs/decisions/0001-python-cli-with-julia-backend.md`](docs/decisions/0001-python-cli-with-julia-backend.md).

## Python tooling — strictly uv

Use **uv** for every environment and dependency operation.

- `uv add <pkg>` / `uv add --dev <pkg>` to add dependencies.
- `uv remove <pkg>` to remove them.
- `uv run <cmd>` to execute commands in the project environment.
- `uv sync` to recreate the environment from the lockfile.
- **Do not** hand-edit `[project.dependencies]` or `[dependency-groups]` in
  `pyproject.toml`; those are owned by `uv add` / `uv remove`.
- **Do** edit `[project]` metadata (including `version`), `[project.scripts]`,
  and tool configuration (`[tool.ruff]`, `[tool.pytest.ini_options]`, …).

## Code style

| Area | Rule |
| --- | --- |
| Python | 3.11+ per `requires-python` |
| Linter / formatter | **ruff** (line length **100**, target **py311**) |
| Type hints | Required on every **public** function and method |
| Docstrings | Google-flavoured on public APIs; module docstring atop each `.py` |
| Imports | ruff isort; absolute imports (`model_parser.…`) |
| Julia | follow the prototype style in `apcplants/ProcessModelingJL`; `Pkg` for deps |

Local checks (must match CI):

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Architecture principles

### Pure logic vs. I/O separation

**Pure modules** parse, normalize, validate, and lower — no filesystem,
subprocess, or network access. Keep `ir/`, `frontends/`, `backends/`, and
`validation/` pure and deterministic.

**I/O modules** read/write files and implement the CLI. `io.py` and `cli.py` own
filesystem access; the CLI must stay a thin shell over the pure functions.

### One transformation ≈ one module

- `frontends/<format>.py` — one authoring format → IR (`parse` + `normalize`).
- `backends/<target>.py` — IR → one target view (`lower` / codegen).
- `validation/` — semantic and profile checks.
- `ir/` — the data model and expression tree; the shared contract.

Adding a backend means **one new `backends/*.py` + tests**, never editing every
other backend (that is the whole point of the hub-and-spoke IR).

### The IR is the single semantic truth

- The IR describes a **scaffold only** (structure + equations + roles + units +
  metadata). Parameter sets and scenarios (incl. initial values `x0`/`u0`) are
  **out of scope** — frontends drop them with a `WARN`.
- The IR is **versioned JSON** (`ir_version`, SemVer). A breaking schema change
  requires migration notes and an ADR.
- Every IR carries a **content hash** over its semantic body; downstream
  artifacts reference scaffolds by hash, not path.
- Expression semantics live in the **explicit expression tree**
  (`ir/expr.py`), never in per-backend string rewrites.

### Codegen, not serialized objects

The durable form of an MTK model is the **IR JSON + generated `.jl` script**,
never a serialized `System`. Generated Julia targets **MTK v11** idioms
(`System(eqs, t)`, `mtkcompile`, `t_nounits`/`D_nounits`, no `@mtkmodel`, no
`structural_simplify`). See ADRs 0002 and 0004.

### Determinism & idempotency

Re-running `parse`/`emit` on unchanged input must produce byte-identical output
(stable ordering, stable number formatting). The content hash depends only on
the semantic body.

### Status vocabulary and exit codes

CLI diagnostics use `OK` · `WARN` · `ERROR`. Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | success; no `ERROR` diagnostics |
| `1` | at least one `ERROR` (e.g. validation failed) |
| `2` | invalid usage / load failure before meaningful work |

### CLI conventions

- Long options in kebab-case (`--from`, `--profile`, `--output`/`-o`).
- The two core verbs are `parse` (authoring → IR) and `emit <target>` (IR →
  view). Supporting commands: `validate`, `inspect`, `ast`, `schema`.
- Breaking CLI changes require a SemVer bump and release notes.

## Scope guardrails

**In scope:** authoring-format parsing, the canonical IR + JSON Schema, semantic
& profile validation, IR↔backend lowering / codegen, conformance fixtures.

**Out of scope:** parameter identification, scenario execution / simulation,
result storage, controller synthesis, deployment, UI. Those are sibling tools
that *consume* the IR.

If a change request conflicts with the design doc, stop and resolve via an
explicit doc + ADR update — do not silently expand scope.

## Testing

- Framework: **pytest** (`uv run pytest`).
- **Unit tests** for pure logic: expression parser, frontend, backend codegen,
  validators.
- **CLI smoke tests** with `typer.testing.CliRunner`.
- **Conformance** (as it grows): an IR fixture plus expected Julia output and/or
  expected trajectories, shared between the Python codegen and `ModelParserJL`.

## Documentation

- `docs/design/` — design notes and the product spec (Markdown).
- `docs/decisions/` — numbered ADRs (`NNNN-title.md`), one decision each, never
  deleted; supersede instead. Index in `docs/decisions/index.md`.
- `docs/chatlogs/` — session summaries (`YYYY-MM-DD_topic.md`) after substantive
  work, with a short *Commit helper* and *How to try* up top.
- `schemas/canonical-ir.schema.json` — the committed, generated IR schema; keep
  it in sync via `uv run model-parser schema -o schemas/canonical-ir.schema.json`.
- No secrets, no customer-specific identifiers; use placeholders.

## Versioning

Follow [SemVer](https://semver.org/). During `0.y.z`, breaking CLI or IR-schema
changes are allowed but must be called out. Keep `project.version` in
`pyproject.toml` and `__version__` in `src/model_parser/__init__.py` identical.

## Commit conventions

- Imperative, concise subjects (`add realtime-cpp profile check`).
- Prefer one logical change per commit.
- [Conventional Commits](https://www.conventionalcommits.org/) shape where it
  helps (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
