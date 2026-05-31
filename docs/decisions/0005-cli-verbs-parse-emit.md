# ADR 0005 — CLI shape: `parse` and `emit <target>` as core verbs

**Status:** accepted · 2026-06-01

## Context

The CLI is the main user-facing surface. It should map cleanly onto the
ecosystem's transformation vocabulary (`parse`, `normalize`, `lower`, `export`,
`validate`) and stay extensible as authoring formats and backends are added,
without reshaping existing commands.

## Decision

Two core verbs mirror the hub-and-spoke model:

- **`parse <authoring-file> [--from <format>] [-o out.ir.json]`** — authoring →
  canonical IR. `--from` selects the frontend (default and only: `exprtk-ini`).
  Combines the `parse` + `normalize` transformations.
- **`emit <target> <model.ir.json> [-o out]`** — canonical IR → a backend view.
  `emit` is a command group so targets are added as subcommands
  (`emit julia` now; `emit cpp`, `emit ini` planned) without touching existing
  ones.

Supporting commands: `validate` (IR or authoring file, optional `--profile`),
`inspect` (human summary), `ast` (debug tree), `schema` (export JSON Schema).

Conventions: kebab-case long options; `-o/--output` defaults to stdout so
commands compose in pipelines. Exit codes `0`/`1`/`2`; diagnostics use
`OK`/`WARN`/`ERROR`.

## Consequences

- + The two verbs match the user's mental model ("turn my INI into IR", "build
  the Julia model from IR") and the org transformation table.
- + Adding a frontend is a `--from` value; adding a backend is an `emit`
  subcommand — both are additive, non-breaking.
- + stdout-by-default keeps commands scriptable and CI-friendly.
- − `emit` as a group is slightly more typing than a flat `emit-julia`; justified
  by clean extensibility.

## Alternatives considered

- *Flat verbs per target (`to-julia`, `to-cpp`).* Rejected: the command set
  grows combinatorially and obscures the shared `lower` transformation.
- *A single `convert --from --to`.* Rejected: harder to give target-specific
  options and help; less discoverable than `emit <target> --help`.
- *Always write files (no stdout).* Rejected: stdout-by-default composes better
  and keeps the tool pipeline-friendly.

## References

- Org architecture: transformations table (`parse`, `normalize`, `lower`,
  `export`, `validate`)
- `apcplants/docs/design/frontend-and-project-structure-options.md` §5
- [`docs/design/model-parser.md`](../design/model-parser.md) §5
