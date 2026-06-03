# Release note drafts

Markdown files in this directory are **maintainer-facing drafts** for GitHub
Releases. They are consumed with:

```bash
gh release create vX.Y.Z --title "…" --notes-file docs/release-notes/vX.Y.Z_short-slug.md
```

See **Session summaries** and **Release notes draft (when a release is proposed)**
in [`AGENTS.md`](../../AGENTS.md) for when to add a file here and how it links from
`docs/chatlogs/`.

**Naming:** `vX.Y.Z_short-slug.md` (ASCII slug; tag on GitHub uses the same
`vX.Y.Z` prefix as in `release.yml`).

These paths are **excluded** from the MkDocs site (`mkdocs.yml` → `exclude_docs`);
they remain visible in the Git repository and in release automation.
