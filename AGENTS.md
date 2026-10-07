# model-parser

- Python CLI (PyPI `apc-model-parser`): ExprTk INI -> canonical IR (JSON) -> Julia MTK, Julia RHS, Python views.
- Verify: `uv sync --all-groups && uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mkdocs build --strict`.
- The IR is the single semantic truth. Expression semantics live only in `ir/expr.py`, never in per-backend string rewrites.
- `ir/`, `frontends/`, `backends/`, `validation/` stay pure (no I/O). A new backend is one `backends/*.py` plus tests.
- Generated Julia targets MTK v11: `System(eqs, t)`, `mtkcompile`; no `@mtkmodel`, no `structural_simplify`. Never serialize a `System`.
- Output must be byte-identical across runs (respect `SOURCE_DATE_EPOCH`).
- After any IR model change, regenerate `schemas/canonical-ir.schema.json`. A breaking IR change bumps `ir_version`.
- Parameter sets, scenarios and `x0`/`u0` are out of scope; frontends drop them with a WARN.
