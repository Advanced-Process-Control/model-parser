# CI/CD and releases

This repository uses **GitHub Actions** under [`.github/workflows/`](https://github.com/Advanced-Process-Control/model-parser/tree/main/.github/workflows).

## Continuous integration (`ci.yml`)

Runs on **push** and **pull_request** to `main` or `master`:

- `uv sync --all-groups`
- `ruff check` / `ruff format --check`
- `pytest`
- `mkdocs build --strict` (documentation must build cleanly)

## Documentation site (`docs.yml`)

Builds **MkDocs** and deploys to **GitHub Pages** when the default branch is updated
(or on **workflow_dispatch**).

**One-time repository setup**

1. **Settings → Pages → Build and deployment**
2. Set **Source** to **GitHub Actions** (not “Deploy from a branch”).

The published URL is:

`https://advanced-process-control.github.io/model-parser/`

(`site_url` in `mkdocs.yml` must stay aligned with that base.)

## PyPI releases (`release.yml`)

Runs on **push** of SemVer tags:

- `vMAJOR.MINOR.PATCH` (e.g. `v0.1.0`)
- Pre-releases matching `vMAJOR.MINOR.PATCH.*` (e.g. `v0.2.0-rc.1`)

The job:

1. Syncs the environment and runs **`uv build`**
2. Uploads `dist/` as a workflow artefact
3. Creates a **GitHub Release** (with generated notes) and attaches the built files
4. Publishes to **PyPI** using **trusted publishing (OIDC)** — no long-lived API token in secrets

After publish, end users typically install the CLI with **`pipx install apc-model-parser`** or **`uv tool install apc-model-parser`** (command on `PATH`: **`model-parser`**).

### PyPI trusted publisher

Configure the pending publisher on PyPI for:

- **Repository:** `Advanced-Process-Control/model-parser`
- **Workflow:** `release.yml`
- **Environment:** if you set **`pypi`** on PyPI, create a matching **GitHub Environment**
  named `pypi` (Settings → Environments) so OIDC claims match. If PyPI leaves
  environment blank, remove or adjust the `environment:` block in `release.yml`
  accordingly.

### GitHub Environment URL

The workflow sets `environment.url` to the PyPI project page for convenience when
viewing deployment status.

### Tagging order

Bump `version` in `pyproject.toml` and `__version__` in `src/model_parser/__init__.py`,
merge to the default branch, then create an **annotated** tag on that commit and
push the tag. See [`AGENTS.md`](https://github.com/Advanced-Process-Control/model-parser/blob/main/AGENTS.md)
for the full release policy.
