---
title: GitHub Actions (CI, MkDocs → Pages, PyPI release) and docs site scaffold
topic: ci-cd-docs
date_added: 2026-06-01
tags: [chatlogs]
links:
  - .github/workflows/ci.yml
  - .github/workflows/docs.yml
  - .github/workflows/release.yml
  - mkdocs.yml
  - docs/index.md
  - docs/api.md
  - docs/deployment/ci-cd.md
  - AGENTS.md
  - README.md
  - pyproject.toml
  - uv.lock
  - .gitignore
---

## Commit helper

- **SemVer / version bump:** **No bump** for this session — infrastructure and
  documentation publishing only; runtime package version stays at `0.1.0` until a
  deliberate release.
- **Tags / GitHub Release:** **None** — merge to `main` first; tag `v0.1.0` (or
  later) when ready to trigger **`release.yml`** and the PyPI trusted publisher.
- **Suggested commit message:** `ci: add GitHub Actions, MkDocs site, and PyPI release workflow`
- **Copy-paste git commands:**

```bash
git add .github/workflows/ci.yml .github/workflows/docs.yml .github/workflows/release.yml \
        mkdocs.yml docs/index.md docs/api.md docs/deployment/ci-cd.md \
        docs/chatlogs/2026-06-01_ci-mkdocs-github-pages-pypi.md \
        pyproject.toml uv.lock AGENTS.md README.md .gitignore
git commit -m 'ci: add GitHub Actions, MkDocs site, and PyPI release workflow'
```

- **Git order when tagging a release:** N/A this session (no tag). When releasing:
  bump `pyproject.toml` + `src/model_parser/__init__.py` → commit/push → then
  `git tag -a vX.Y.Z` → `git push origin vX.Y.Z`.

## How to try

```bash
cd /path/to/model-parser
uv sync --all-groups
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mkdocs build --strict

# After push to main: enable GitHub Pages (Settings → Pages → GitHub Actions),
# then open the deployed site (see docs/deployment/ci-cd.md for URL).
```

## Session narrative

**Goal.** Add repoman-style automation: **CI** on `main`/`master`, **strict MkDocs**
in CI, **GitHub Pages** deployment for the public docs site, and **`release.yml`**
for **`uv build`** + GitHub Release assets + **PyPI** via **OIDC** (`apc-model-parser`,
workflow name aligned with the pending trusted publisher).

**Shipped surface.**

- **Workflows:** `ci.yml` (ruff, pytest, `mkdocs build --strict`), `docs.yml`
  (build + `deploy-pages`), `release.yml` (tag filter matching SemVer and
  pre-releases, `softprops/action-gh-release`, `pypa/gh-action-pypi-publish`,
  environment **`pypi`** + PyPI project URL).
- **MkDocs:** root `mkdocs.yml` (Material, mkdocstrings with `paths: [src]`,
  `exclude_docs: chatlogs/**`), `docs/index.md`, `docs/api.md` (`::: model_parser`),
  `docs/deployment/ci-cd.md` for maintainer setup (Pages source, PyPI environment
  caveats, tag order).
- **Dependencies:** dev group extended via `uv add` with `mkdocs`, `mkdocs-material`,
  `mkdocstrings[python]`; `uv.lock` updated.
- **Repo hygiene:** `.gitignore` includes `site/`; **AGENTS.md** / **README.md**
  updated so local checks and contributor docs match CI.

**Follow-ups for maintainers.** Create GitHub **Environment** `pypi` if PyPI’s
trusted publisher expects it (or drop `environment:` from `release.yml` if PyPI
has no environment name). One-time **Pages → GitHub Actions** source selection.
