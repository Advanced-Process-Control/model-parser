# Decision log

Architectural Decision Records (ADRs) for **model-parser**. Each ADR is short,
dated, pinned to a status, and never deleted — superseded instead.

These are **repository-level** decisions. Organization-wide decisions live in
the `.github` architecture decision log (rich HTML communication artifacts, per
org ADR 0004). Repo-level ADRs are kept as Markdown here so they sit next to the
code and review naturally in pull requests.

## Active ADRs

| # | Title | Status | Date |
|---|---|---|---|
| [0001](0001-python-cli-with-julia-backend.md) | Python CLI with a Julia backend, IR as the boundary | accepted | 2026-06-01 |
| [0002](0002-codegen-over-serialized-system.md) | Generate Julia code; do not serialize the MTK `System` | accepted | 2026-06-01 |
| [0003](0003-explicit-expression-ir.md) | Explicit expression IR, not string rewrites | accepted | 2026-06-01 |
| [0004](0004-target-mtk-v11-idioms.md) | Generated Julia targets ModelingToolkit v11 idioms | accepted | 2026-06-01 |
| [0005](0005-cli-verbs-parse-emit.md) | CLI shape: `parse` and `emit <target>` as core verbs | accepted | 2026-06-01 |

## Format

Each ADR uses the same six sections, in order, kept short: **Status**,
**Context**, **Decision**, **Consequences**, **Alternatives considered**,
**References**.

## Process

1. Open a draft ADR with the next sequential id; status starts `proposed`.
2. Discuss in the implementing PR.
3. On acceptance, mark `accepted` and date it.
4. When a later ADR replaces it, mark the old one `superseded by #NNNN` and
   leave it readable. Never delete an ADR.
