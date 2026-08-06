---
title: Python numerical model view and model-library sync
topic: codegen
date_added: 2026-08-06
tags: [chatlogs]
links:
  - docs/design/model-parser.md
  - docs/decisions/0007-python-numerical-view.md
  - docs/release-notes/v0.2.3_python-model-view.md
  - src/model_parser/backends/python.py
  - src/model_parser/cli.py
---

## Commit helper

- **SemVer / version bump:** **PATCH** (`0.2.2` to `0.2.3`) - additive CLI target and public backend API; no IR change.
- **Tags / GitHub Release:** Tag after bump as `v0.2.3`; pushing the tag runs `release.yml` and publishes to PyPI.
- **Suggested commit message:** `feat(emit): add Python numerical model view`
- **Release notes:** [`v0.2.3_python-model-view.md`](../release-notes/v0.2.3_python-model-view.md)
- **Git order when tagging:** commit and push `main`, create annotated `v0.2.3`, then push the tag.

```bash
git add AGENTS.md README.md docs examples mkdocs.yml pyproject.toml \
  src/model_parser tests
git commit -m 'feat(emit): add Python numerical model view'
git push origin main
git tag -a v0.2.3 -m 'v0.2.3'
git push origin v0.2.3
gh release create v0.2.3 --title "v0.2.3 - Python model view" \
  --notes-file docs/release-notes/v0.2.3_python-model-view.md
```

## How to try

```bash
uv run model-parser parse examples/models/model_monod_simple.ini -o /tmp/monod.ir.json
uv run model-parser emit python /tmp/monod.ir.json -o /tmp/monod.py
uv run pytest tests/test_python.py tests/test_cli.py
```

## Session narrative

**Goal:** Add an executable Python model view and keep the sibling model library
as the database of generated representations.

**Shipped:** A pure Python expression/codegen backend, the `emit python` CLI
target, executable numerical tests, ADR 0007, version `0.2.3`, release notes,
and model-library sync/lock support for `views/model.py`.

**Decision:** Generated RHS functions use SciPy argument order and declaration-
order sequences while remaining independent of NumPy and SciPy.

**Follow-up:** Add cross-language trajectory fixtures when the conformance suite
is expanded beyond generated-code execution checks.