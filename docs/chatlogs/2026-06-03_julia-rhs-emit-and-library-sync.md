---
title: Julia numerical RHS emit target and model-library sync
topic: codegen
date_added: 2026-06-03
tags: [chatlogs]
links:
  - AGENTS.md
  - docs/design/model-parser.md
  - docs/decisions/0006-julia-numerical-rhs-view.md
  - src/model_parser/backends/julia_expr.py
  - src/model_parser/backends/julia_rhs.py
  - src/model_parser/cli.py
---

## Commit helper

- **SemVer / version bump:** **PATCH** (`0.2.1` → `0.2.2`) — new CLI subcommand `emit julia-rhs` and new public Python API `emit_julia_rhs`; backward-compatible for existing `emit julia` users.
- **Tags / GitHub Release:** **None** — stack on default branch; tag when cutting a PyPI release (existing `release.yml` on tag).
- **Suggested commit message (model-parser repo):** `feat(emit): add julia-rhs numerical ODE view`
- **Copy-paste git commands (model-parser):**

```bash
cd /path/to/model-parser
git add AGENTS.md README.md docs/design/model-library-and-versioning.md \
  docs/design/model-parser.md docs/design/storing-mtk-models.md \
  docs/decisions/0006-julia-numerical-rhs-view.md docs/decisions/index.md \
  docs/chatlogs/2026-06-03_julia-rhs-emit-and-library-sync.md \
  examples/README.md examples/run.sh mkdocs.yml pyproject.toml \
  src/model_parser/__init__.py src/model_parser/backends/__init__.py \
  src/model_parser/backends/julia_expr.py src/model_parser/backends/julia_mtk.py \
  src/model_parser/backends/julia_rhs.py src/model_parser/cli.py \
  tests/test_cli.py tests/test_julia_rhs.py
git commit -m "$(cat <<'EOF'
feat(emit): add julia-rhs numerical ODE view

Share IR→Julia expression lowering in julia_expr; emit f!/outputs! codegen;
document packing and ADR 0006; extend examples and model-library design notes.
EOF
)"
```

- **Suggested commit message (model-library repo, separate clone):** `chore(views): add model_rhs.jl and lock digests from emit julia-rhs`
- **Copy-paste git commands (model-library):**

```bash
cd /path/to/model-library
git add README.md library.lock.json scripts/sync.sh scripts/update_lock.py \
  models/*/model.ir.json models/*/views/model.jl models/*/views/model_rhs.jl
git commit -m "$(cat <<'EOF'
chore(views): sync numerical RHS views and lockfile

Regenerate IR/MTK views; add model_rhs.jl and julia_rhs_* lock fields per sync.
EOF
)"
```

- **Git order when tagging:** commit / push branch (with version bump if releasing) → annotated tag on that commit → push tag.

## How to try

```bash
cd /path/to/model-parser
uv sync --all-groups
uv run model-parser parse examples/models/model_monod_simple.ini -o /tmp/m.ir.json
uv run model-parser emit julia-rhs /tmp/m.ir.json
uv run pytest tests/test_julia_rhs.py tests/test_cli.py
uv run mkdocs build --strict
```

**model-library:** `MODEL_PARSER_VENV=/path/to/model-parser/.venv ./scripts/sync.sh` then inspect `models/*/views/model_rhs.jl` and `library.lock.json`.

## Session narrative

**Goal:** Implement a second Julia backend that emits an explicit numerical RHS (`f!` and optional `outputs!`) from the canonical IR, and wire the sibling `model-library` sync + lockfile to generate and fingerprint `views/model_rhs.jl`.

**Shipped (model-parser):** New module `julia_expr.py` (shared `expr_to_julia`, `julia_model_slug`, `julia_number_literal`, `JuliaCodegenError`); `julia_mtk.py` refactored to use it; `julia_rhs.py` with `emit_julia_rhs`; CLI `emit julia-rhs`; tests; PATCH version bump; ADR 0006; design/README/AGENTS/examples updates; MkDocs nav entry.

**Shipped (model-library):** `sync.sh` runs `emit julia-rhs` to `views/model_rhs.jl`; `update_lock.py` records `julia_rhs_relpath` and `julia_rhs_content_hash`; README updated; all models re-synced (committed artifacts include new `.jl` files and refreshed lock).

**Follow-ups:** Optional `ApcModelAnalysis.jl` helper to load `model_rhs.jl`; conformance tests comparing MTK trajectory vs plain `ODEProblem` built from `f!` for small fixtures.
