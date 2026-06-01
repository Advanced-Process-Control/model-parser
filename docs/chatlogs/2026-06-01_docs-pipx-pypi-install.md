---
title: Document PyPI CLI install (pipx and uv tool)
topic: docs-packaging
date_added: 2026-06-01
tags: [chatlogs]
links:
  - README.md
  - docs/index.md
  - docs/deployment/ci-cd.md
  - AGENTS.md
---

## Commit helper

- **SemVer / version bump:** **No bump** — documentation only; no change to the
  published package API or CLI contract beyond how to install it.
- **Tags / GitHub Release:** **None** — stack on `main`; releases remain tag-driven
  when version/metadata changes warrant a new **`v*.*.*`**.
- **Suggested commit message:** `docs: document pipx and uv tool install for apc-model-parser`
- **Copy-paste git commands:**

```bash
git add README.md docs/index.md docs/deployment/ci-cd.md AGENTS.md \
        docs/chatlogs/2026-06-01_docs-pipx-pypi-install.md
git commit -m 'docs: document pipx and uv tool install for apc-model-parser'
```

- **Git order when tagging a release:** N/A this session.

## How to try

```bash
pipx install apc-model-parser
model-parser --help

# Alternative (same CLI, different installer):
# uv tool install apc-model-parser

# Docs site (after deploy):
# uv run mkdocs build --strict
```

## Session narrative

**Goal.** After the first PyPI publish and manual **`v0.1.0`** tag, document that
end users can install the CLI with **`pipx install apc-model-parser`**, not only
**`uv tool install`**, while keeping **`apc-model-parser`** vs **`model-parser`**
(dist name vs command) explicit.

**Shipped surface.**

- **`README.md`:** Install split into **CLI from PyPI** (`pipx` primary, `uv tool`
  comment) and **from source** (`uv sync --all-groups`).
- **`docs/index.md`:** Published site home — same dual path for PyPI installs;
  short note that both are isolated env installs with `model-parser` on `PATH`.
- **`docs/deployment/ci-cd.md`:** One line after the release job listing consumer
  **`pipx`** / **`uv tool install`** post-publish.
- **`AGENTS.md`:** Documentation layout bullet updated to mention PyPI install via
  **`pipx` / `uv tool`** and dev via **`uv`**.

**Follow-ups.** None required; optional future “Getting started” page could repeat
install if the nav grows.
