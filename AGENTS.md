# Coding agent guidelines for model-parser

This file defines how AI coding agents (e.g. Cursor, Copilot) and human
contributors collaborate on this repository. Human reviewers should treat it as
the canonical contributor guide. It is **public**: describe behaviour only in
terms of this project and its published design — avoid internal codenames or
unrelated repositories.

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

## Platform and paths

- **Targets:** Linux, macOS, and Windows where the CLI runs. Prefer `pathlib`,
  avoid hard-coded host-specific paths in tests and examples; use `tmp_path` in
  pytest and placeholders in docs (`/tmp`, `example.ini`).
- **Julia side:** `julia/ModelParserJL/` must remain loadable on the supported
  Julia versions stated in that package; document any extra env assumptions in
  the design doc or `examples/README.md`.

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
- `uv sync` / `uv sync --all-groups` to recreate the environment from the
  lockfile (use **`--all-groups`** so dev dependencies match CI).
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
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run mkdocs build --strict
```

## Architecture principles

### Pure logic vs. I/O separation

**Pure modules** parse, normalize, validate, and lower — no filesystem,
subprocess, or network access. Keep `ir/`, `frontends/`, `backends/`,
`semantic_diff.py`, and `validation/` pure and deterministic.

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
the semantic body. For `provenance.created_at`, when `SOURCE_DATE_EPOCH` is set
(see reproducible-builds.org), the INI frontend uses that instant instead of the
wall clock so regenerated IR JSON stays stable when semantics are unchanged.

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
  view). Supporting commands: `validate`, `inspect`, `diff`, `bump`, `ast`,
  `schema`.
- Breaking CLI changes require a SemVer bump and release notes.

## Scope guardrails

**In scope:** authoring-format parsing, the canonical IR + JSON Schema, semantic
& profile validation, IR↔backend lowering / codegen, conformance fixtures.

**Out of scope:** parameter identification, scenario execution / simulation,
result storage, controller synthesis, deployment, UI. Those are sibling tools
that *consume* the IR.

If a change request conflicts with the design doc, stop and resolve via an
explicit doc + ADR update — do not silently expand scope.

## Work tracking (ADRs, issues, and todos)

- **ADRs:** numbered files under [`docs/decisions/`](docs/decisions/) (`NNNN-title.md`),
  indexed in [`docs/decisions/index.md`](docs/decisions/index.md). One decision per
  file; never delete — supersede with a newer ADR and update the index.
- **Issues:** use GitHub issues for backlog items that are not yet an ADR; link
  ADRs from issue/PR text when a decision motivates the change.
- **Todo briefs:** theme-sized notes under [`docs/todo/`](docs/todo/) (`index.md` +
  one file per theme); promote into ADRs or design docs when behaviour is
  decided. Not a substitute for issues or ADRs.
- Prefer **small, reviewable slices** (one coherent feature, bugfix, or refactor
  per PR when practical). For larger work, split PRs and reference the same ADR
  or design section in each.

### Recommended slice workflow (maintainers & agents)

1. **Align scope** — confirm design doc + ADR if behaviour or IR contract changes.
2. **Implement & test** — code and automated tests for that slice; keep pure vs I/O
   boundaries intact.
3. **Verify locally** — `uv sync --all-groups`, ruff check/format, `uv run pytest`,
   `uv run mkdocs build --strict` (same as CI).
4. **Docs** — update `docs/design/model-parser.md`, schema regeneration command, or
   ADR in the **same** change series when the public contract moves.
5. **`docs/chatlogs/…`** when the slice materially changes behaviour or governance.

## Testing

- Framework: **pytest** (`uv run pytest`).
- **Unit tests** for pure logic: expression parser, frontend, backend codegen,
  validators.
- **CLI smoke tests** with `typer.testing.CliRunner`.
- **Conformance** (as it grows): an IR fixture plus expected Julia output and/or
  expected trajectories, shared between the Python codegen and `ModelParserJL`.

## Documentation system

**Target stack** (align when a docs site is added): **MkDocs** with the **Material**
theme and **mkdocstrings** (or equivalent) for Python API reference; Julia API
docs may stay in `julia/ModelParserJL/` README until unified.

**Intended layout** (keep consistent with [`docs/design/model-parser.md`](docs/design/model-parser.md)):

- `docs/index.md` or root `README.md` — overview, install (PyPI via `pipx` / `uv tool`, dev via `uv`), quick `parse` /
  `emit` examples (when expanded).
- `docs/design/` — product spec (`model-parser.md`) and deep architecture notes.
- `docs/decisions/` — ADRs (`NNNN-title.md`) + `index.md`.
- `docs/chatlogs/` — session summaries (see **Session summaries** below).
- `docs/deployment/` — optional summaries for CI/CD, packaging, and release
  process once those exist in-repo.

**Rules:**

- User-facing prose lives under `docs/`; IR semantics and the CLI contract stay
  accurate relative to the design doc and JSON Schema.
- Do not commit secrets, real tokens, or customer-specific identifiers; use
  placeholders (`example.com`, generic model names).
- Once `mkdocs.yml` exists, CI **should** run `uv run mkdocs build --strict`; until
  then, Markdown in `docs/` remains valid without a site build.

**Generated artefacts:**

- [`schemas/canonical-ir.schema.json`](schemas/canonical-ir.schema.json) is
  committed output; regenerate with  
  `uv run model-parser schema -o schemas/canonical-ir.schema.json`  
  whenever the IR Pydantic models change, in the same change series as the code.

## Runnable examples (`examples/`)

- Keep **small, well-commented, copy-paste-friendly** inputs under
  [`examples/models/`](examples/models/) and expected outputs under
  [`examples/outputs/`](examples/outputs/) where helpful for reviewers and users
  (not only pytest).
- Prefer **English** comments and placeholders — never real proprietary model text
  or secrets.
- When a session ships **user-visible CLI or IR** behaviour, add or refresh an
  **`examples/…`** entry in the **same** merge series as the chatlog when feasible.
- Document how to run examples in [`examples/README.md`](examples/README.md)
  (e.g. `examples/run.sh`, `uv run model-parser …`).

## Session summaries (`docs/chatlogs/`)

**Required** after substantive sessions (multi-step implementation, non-trivial
design discussion, or when behaviour or doc intent shifts).

### Commit helper (mandatory placement)

Every chatlog MUST begin with a **`## Commit helper`** section (level-2 heading).

**Order of file contents**

1. **YAML frontmatter** (when used) MUST be the **first bytes** of the file (`---` … `---`).
2. Immediately after the closing `---`, **`## Commit helper`** MUST be the **first
   Markdown body content** — nothing above it except frontmatter.
3. Next, **`## How to try`** MUST follow **`## Commit helper`** (not the long narrative).
4. If frontmatter is omitted, **`## Commit helper`** is the first line, then **`## How to try`**, then the narrative.

**Commit helper MUST contain**

- **`SemVer / version bump`:** **no bump** vs **PATCH / MINOR / MAJOR**, tied to
  what shipped (docs-only vs user-visible CLI/IR vs breaking schema or CLI). See
  [**Versioning, releases, and release notes**](#versioning-releases-and-release-notes).
- **`Tags / GitHub Release`:** always fill — **None** (stack on default branch) or
  **Tag after bump** with exact tag string (e.g. `v0.2.0`), pre-release if needed,
  and whether a **`release.yml`** (or future) workflow should run on tag push.
- **Suggested commit message:** one imperative subject; optional Conventional scope
  (`feat(cli): …`, `fix(ir): …`). Use `BREAKING CHANGE:` footer when applicable.
- **Copy-paste git commands:** fenced `bash` with `git add` paths and
  `git commit -m '…'`. If the version bump belongs in the same commit, note updates
  to `pyproject.toml` and `src/model_parser/__init__.py`.
- **Git order when tagging:** never tag before the release commit exists locally:
  **commit / push branch (with version bump)** → **`git tag -a vX.Y.Z` on that
  commit** → **`git push origin vX.Y.Z`**.

### How to try (mandatory unless N/A)

Immediately after **`## Commit helper`**, include **`## How to try`** with concrete
`uv run model-parser …` steps, pytest selection, or `examples/…` commands. For
pure docs/chatlog hygiene: **`N/A (docs-only).`**

### Session narrative

After **How to try**, summarize shipped modules, CLI/IR edge cases, and regression
risks in English (**goal → shipped surface → decisions → follow-ups**).

**Naming:** `YYYY-MM-DD_short-topic.md` (ASCII slug).

**Frontmatter (YAML):** at least `title`, `topic`, `date_added`, `tags: [chatlogs]`,
and `links:` to touched specs or code (e.g. `AGENTS.md`, `docs/design/model-parser.md`).

**Not a substitute for:** ADRs, tests, or commit messages — those remain the source
of truth for the contract.

## CI/CD (GitHub Actions)

Workflows live under [`.github/workflows/`](.github/workflows/). Maintainer-facing
detail (Pages setup, PyPI trusted publishing, tag order) is in
[`docs/deployment/ci-cd.md`](docs/deployment/ci-cd.md).

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| [`ci.yml`](.github/workflows/ci.yml) | Push / PR to `main` or `master` | `uv sync --all-groups`, ruff, pytest, **`mkdocs build --strict`** |
| [`docs.yml`](.github/workflows/docs.yml) | Push to `main`/`master`, `workflow_dispatch` | Build MkDocs and deploy to **GitHub Pages** |
| [`release.yml`](.github/workflows/release.yml) | Push SemVer tags `vX.Y.Z` (and pre-release suffixes) | `uv build`, GitHub Release + assets, **PyPI** (OIDC) |

**Rules:**

- CI commands must be reproducible locally (`uv run …`); the **local check block**
  above must stay aligned with `ci.yml`.
- **PyPI** uses **trusted publishing** via `pypa/gh-action-pypi-publish` with GitHub
  **environment** `pypi` — configure the same environment name on PyPI’s pending
  publisher (or adjust the workflow if PyPI omits environment). Distribution name:
  **`apc-model-parser`**; import package and CLI: **`model_parser`** / `model-parser`.
- **GitHub Pages:** repository **Settings → Pages → Source: GitHub Actions** (one-time).
  Published site: `https://advanced-process-control.github.io/model-parser/` (must
  match `site_url` in `mkdocs.yml`).

## Versioning, releases, and release notes

### Semantic versioning

Follow **[Semantic Versioning 2.0.0](https://semver.org/)** (`MAJOR.MINOR.PATCH`).

- **`0.y.z`:** breaking CLI or IR schema changes are allowed but must be called out
  in release notes and usually accompanied by an ADR.
- **`1.0.0` onward:** honour SemVer for the **documented** public surface: stable
  CLI flags, `ir_version`, JSON Schema compatibility as advertised.

### Single source of truth for the running version

Bump **both** in the same release series until tooling ties them automatically:

- `project.version` in [`pyproject.toml`](pyproject.toml)
- `__version__` in [`src/model_parser/__init__.py`](src/model_parser/__init__.py)

Keep them identical for each release tag.

### Tags and GitHub Releases

- **Ordering:** merge the commit(s) that bump version fields; **then** create an
  **annotated** tag **`vX.Y.Z`** on **that** commit; **then** `git push origin vX.Y.Z`.
  Release automation (when added) should trigger on tag push; the leading `v` is
  a common convention — match whatever `release.yml` expects.
- **Release notes:** use GitHub auto-generated notes where helpful; edit for IR or
  CLI highlights.
- **Optional `CHANGELOG.md`:** if introduced, follow
  [Keep a Changelog](https://keepachangelog.com/) and update it in the release
  commit series.

### Artefacts

- **`uv build`** produces `dist/*.tar.gz` and `dist/*.whl`. A release workflow can
  attach them to GitHub Releases and PyPI.
- **Wheel tags** and `requires-python` must match actual dependency and runtime
  support; adjust classifiers in `pyproject.toml` as the project matures.

### Pre-releases

Pre-release tags (e.g. `v0.2.0-rc.1`, PEP 440–compatible) are fine for testers.
Mark GitHub Releases as **pre-release** when behaviour or schema is unstable.

## Security

- Never commit secrets (tokens, private URLs with embedded credentials).
- Logs and user-visible errors must not echo full file contents of untrusted inputs
  at high verbosity without care — follow the design doc for diagnostic redaction
  policy as it evolves.
- Generated Julia/C++ must not embed secrets from authoring files; treat IR JSON as
  shareable engineering data unless the org classifies it otherwise.

## Commit conventions

- Imperative, concise subjects (`add mtk v11 emit path`, not `added path`).
- Prefer one logical change per commit.
- Reference GitHub issues or ADR filenames when it aids traceability.
- [Conventional Commits](https://www.conventionalcommits.org/) shape where it
  helps (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`).
