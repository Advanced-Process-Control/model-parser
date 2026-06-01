---
title: Tracked todo briefs under docs/todo and MkDocs nav
topic: documentation
date_added: 2026-06-03
tags: [chatlogs]
links:
  - AGENTS.md
  - docs/todo/index.md
  - mkdocs.yml
  - docs/index.md
---

## Commit helper

- **SemVer / version bump:** **no bump** — documentation and contributor-guide updates only (`docs/todo/**`, `mkdocs.yml`, `docs/index.md`, `AGENTS.md`). No user-visible CLI or IR contract change.
- **Tags / GitHub Release:** **None** — stack on default branch.
- **Suggested commit message:** `docs: add tracked todo backlog under docs/todo`
- **Copy-paste git commands:**

```bash
git add AGENTS.md docs/index.md docs/todo/ mkdocs.yml \
  docs/chatlogs/2026-06-03_docs-todo-backlog-mkdocs.md
git commit -m "$(cat <<'EOF'
docs: add tracked todo backlog under docs/todo

Add theme-sized future-work briefs, MkDocs Future work nav, and AGENTS work-tracking note.
EOF
)"
```

- **Git order when tagging:** N/A (no release in this slice).

## How to try

```bash
cd /path/to/model-parser
uv run mkdocs build --strict
# optional: open docs/todo/index.md in the editor or browse site → Future work
```

## Session narrative

**Goal:** Add a `docs/todo/` area with one Markdown file per major future implementation theme, wired into the published docs site, and record guidance on whether `model-library`’s `sync.sh` should auto-commit/push (recommendation: keep sync as regenerate-only; optional separate commit helper; avoid default auto-push).

**Shipped:** `docs/todo/index.md` plus seven task files (`emit-ini-round-trip`, `emit-cpp-realtime-backend`, `ir-schema-migrations`, `parameter-set-contract-cli`, `conformance-fixtures-parity`, `ini-dimensions-inference`, `diff-bump-hardening`); `mkdocs.yml` **Future work** nav listing all pages (satisfies `--strict`); link from `docs/index.md`; `AGENTS.md` **Work tracking** section renamed to include todo briefs and clarify they complement ADRs/issues. MkDocs strict fixes: removed invalid links from `docs/` into `src/` / repo root; use code spans or in-repo doc links only.

**Follow-ups:** Optional `model-library` script `sync-and-commit.sh` (opt-in commit, no default push) if maintainers want scripted commits; promote individual todo themes into GitHub issues or ADRs when scoped.
