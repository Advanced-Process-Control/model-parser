---
title: Model library design, diff/bump CLI, and model-library bootstrap
topic: documentation
date_added: 2026-06-02
tags: [chatlogs]
links:
  - AGENTS.md
  - docs/design/model-parser.md
  - docs/design/model-library-and-versioning.md
  - src/model_parser/cli.py
  - src/model_parser/semantic_diff.py
  - src/model_parser/frontends/exprtk_ini.py
---

## Commit helper

- **SemVer / version bump:** **MINOR** — user-visible CLI (`diff`, `bump`), new pure module `semantic_diff.py`, and `SOURCE_DATE_EPOCH` behaviour for `provenance.created_at` are new public behaviour (not docs-only).
- **Tags / GitHub Release:** **None** — stack on default branch; tag when maintainers cut a release (existing `release.yml` on tag).
- **Suggested commit message:** `feat(cli): add IR diff/bump and model-library design doc`
- **Copy-paste git commands:**

```bash
git add AGENTS.md README.md docs/design/model-library-and-versioning.md \
  docs/design/model-parser.md docs/design/ir-specification.md \
  docs/index.md docs/chatlogs/2026-06-02_model-library-docs-diff-bump.md \
  mkdocs.yml src/model_parser/cli.py src/model_parser/semantic_diff.py \
  src/model_parser/frontends/exprtk_ini.py tests/test_cli.py tests/test_semantic_diff.py
git commit -m "$(cat <<'EOF'
feat(cli): add IR diff/bump and model-library design doc

Add semantic comparison and advisory SemVer bump; document library workflows;
honour SOURCE_DATE_EPOCH for reproducible IR provenance timestamps.
EOF
)"
```

- **Git order when tagging:** commit / push branch (with version bump if releasing) → annotated tag on that commit → push tag.

## How to try

```bash
cd /path/to/model-parser
uv sync --all-groups
uv run model-parser parse examples/models/model_monod_simple.ini -o /tmp/a.ir.json
uv run model-parser parse examples/models/model_monod_simple.ini -o /tmp/b.ir.json
uv run model-parser diff /tmp/a.ir.json /tmp/b.ir.json
uv run model-parser bump /tmp/a.ir.json /tmp/b.ir.json --json
SOURCE_DATE_EPOCH=946684800 uv run model-parser parse examples/models/model_monod_simple.ini -o /tmp/c.ir.json
uv run pytest tests/test_semantic_diff.py
uv run mkdocs build --strict
```

Sibling repo `model-library`: set `MODEL_PARSER_VENV` to this repo’s `.venv` and run `./scripts/sync.sh` (see that repo’s README).

## Session narrative

**Goal:** Capture the prior design answer in-repo, add `diff` / `bump` to support a versioned model library, and bootstrap `Advanced-Process-Control/model-library` with the two existing example models.

**Shipped:** New design page `docs/design/model-library-and-versioning.md` (hashes vs SemVer vs git, workflows, authoring vs parameter sets, optimal multi-file layout, reproducible timestamps); nav and cross-links (`mkdocs.yml`, `docs/index.md`, `model-parser.md`, `ir-specification.md`); `src/model_parser/semantic_diff.py` with conservative bump policy; CLI commands `diff` and `bump` (`--json`); INI frontend respects `SOURCE_DATE_EPOCH` for `provenance.created_at`; tests (`tests/test_semantic_diff.py`, CLI smoke); README and `AGENTS.md` updates.

**model-library repo:** Added `models/monod_simple` and `models/thermal_tank` with copied authoring INIs, `scripts/sync.sh` + `scripts/update_lock.py`, committed generated `model.ir.json` / `views/model.jl`, `library.lock.json`, README, and GitHub Actions CI that installs `model-parser` from git `main` and fails on drift after sync.

**Follow-ups:** Optional ADR for bump policy; `emit ini` and parameter-set JSON remain roadmap; publish a PyPI release so CI can pin a version instead of `main` if desired.
