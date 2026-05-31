---
title: Bootstrap model-parser (IR hub, ExprTk-INI frontend, Julia codegen)
topic: bootstrap
date_added: 2026-06-01
tags: [chatlogs]
links:
  - AGENTS.md
  - README.md
  - docs/design/model-parser.md
  - docs/design/ir-specification.md
  - docs/design/language-strategy.md
  - docs/design/storing-mtk-models.md
  - docs/decisions/index.md
---

## Commit helper

- **SemVer / version bump:** initial scaffold at `0.1.0` (no prior release). No
  bump needed beyond establishing `0.1.0` in `pyproject.toml` and
  `src/model_parser/__init__.py`.
- **Tags / GitHub Release:** None for this session — bootstrap commit on `main`;
  tag a release once the IR schema and conformance fixtures stabilize.
- **Suggested commit message:** `feat: bootstrap model-parser (canonical IR, ExprTk-INI frontend, Julia codegen)`
- **Copy-paste git commands:**

```bash
git add AGENTS.md README.md .gitignore pyproject.toml uv.lock \
        src tests examples schemas julia docs
git commit -m 'feat: bootstrap model-parser (canonical IR, ExprTk-INI frontend, Julia codegen)'
```

## How to try

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .

# Full pipeline on the bundled examples:
./examples/run.sh

# Or step by step:
uv run model-parser parse examples/models/model_monod_simple.ini -o monod.ir.json
uv run model-parser validate monod.ir.json --profile julia-analysis
uv run model-parser emit julia monod.ir.json
```

## Session narrative

**Goal.** Stand up the `model-parser` repository: define what it does (convert
model definitions to/from a canonical IR), choose the language strategy, build a
working MVP, and record the design as docs + numbered ADRs.

**Shipped surface.**

- **IR data model** (`src/model_parser/ir/`): Pydantic models for the scaffold
  (`IRModel`, variables, parameters, locals, equations, provenance) and an
  explicit expression tree (`Num`/`Sym`/`Call`). JSON Schema is generated from
  the model.
- **ExprTk-INI frontend** (`frontends/exprtk_ini.py` + `expr_parser.py`): a real
  tokenizer + precedence-climbing parser (no string rewrites) that normalizes
  `pow`→`^`, `if`→`ifelse`, unary `neg`, and produces the IR. `[x0]`/`[u0]`
  initial values are dropped with a `WARN` (scenario data, not scaffold).
- **Julia/MTK backend** (`backends/julia_mtk.py`): generates a v11-idiomatic
  `.jl` model (`System(eqs, t)`, `mtkcompile`, `t_nounits`/`D_nounits`, no
  `@mtkmodel`, `Float64` literals).
- **Validation** (`validation/validators.py`): semantic checks (undeclared /
  duplicate symbols, missing equations, local ordering) and profile checks
  (`julia-analysis`, `realtime-cpp`).
- **CLI** (`cli.py`, Typer): `parse`, `emit julia`, `validate`, `inspect`,
  `ast`, `schema`. Exit codes 0/1/2; `OK`/`WARN`/`ERROR` diagnostics.
- **Julia companion** (`julia/ModelParserJL`): loads IR JSON → in-memory MTK
  `System` (the conformance/dynamic path complementing codegen).
- **Docs**: product spec, IR spec, language strategy, storing-MTK-models; five
  ADRs (0001–0005); this chatlog. **AGENTS.md** adapted from the repoman guide.
- **Examples**: monod + thermal-tank INI, `run.sh`, committed
  `schemas/canonical-ir.schema.json`.

**Decisions** (see `docs/decisions/`): Python CLI + Julia backend with the IR
JSON as the boundary (0001); codegen over serialized `System` (0002); explicit
expression IR (0003); target MTK v11 idioms (0004); `parse` / `emit <target>`
CLI shape (0005).

**Verification.** `uv run pytest` → 28 passing; `ruff check`/`format` clean;
`./examples/run.sh` produces IR + `.jl` for both example models. Julia codegen
output was reviewed against the working `ProcessModelingJL` v11 patterns; a live
`mtkcompile` run is left to CI with Julia available.

**Follow-ups.** Conformance fixtures shared by the Python codegen and
`ModelParserJL`; `emit ini` / IR `export` round-trip; the `emit cpp` backend for
the `realtime-cpp` profile; richer units/bounds in the IR schema.
