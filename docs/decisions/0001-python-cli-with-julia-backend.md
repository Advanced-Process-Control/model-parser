# ADR 0001 — Python CLI with a Julia backend, IR as the boundary

**Status:** accepted · 2026-06-01

## Context

The work in this repository spans two domains with different natural languages:
(1) text/structure work — tokenizing an authoring grammar, building an AST,
normalizing to an IR, validating, serializing, and generating code; and
(2) symbolic/numeric work — turning the IR into a ModelingToolkit `System` and
analyzing it. Forcing both into one runtime is awkward: a pure-Julia tool would
make the parser carry a heavy symbolic dependency and weak CLI ergonomics, while
a pure-Python tool cannot build MTK systems at all. The org repository map
already anticipates a Python orchestration CLI and a shared IR.

## Decision

Use **both languages, with the canonical IR JSON file as the boundary**:

- **Python** owns the CLI, the expression parser/AST, the IR data model + JSON
  Schema (Pydantic), validators, and the **codegen** backend (IR → `.jl`).
- **Julia** (`julia/ModelParserJL`) owns the in-memory IR → `System` build and
  acts as the conformance/analysis reference.
- Neither language imports the other. They communicate **only** through the IR
  JSON, a language-neutral artifact.

## Consequences

- + `parse`/`emit` need no Julia runtime — fast, dependency-light, CI-friendly.
- + The symbolic work stays idiomatic Julia; the parsing/CLI work stays
  idiomatic Python.
- + Adding a non-Julia backend (e.g. C++) is symmetric: another renderer of the
  same IR.
- − Two toolchains to set up (uv for Python, Pkg for Julia). Mitigated by making
  each path independently usable.
- − Expression semantics could drift between the codegen and the Julia loader;
  mitigated by IR-level conformance fixtures and ADR 0003.

## Alternatives considered

- *Pure Julia (extend `ProcessModelingJL`).* Rejected as the home for the CLI/IR:
  weaker CLI/JSON-schema ergonomics and couples orchestration to the symbolic
  runtime. (It remains the prototype and the reference for the Julia path.)
- *Pure Python with PyJulia/juliacall calling MTK.* Rejected: adds a heavy,
  brittle in-process bridge and a Julia runtime requirement to every `parse`.
- *One language for everything.* Rejected: no single language is strong at both
  ends without significant cost.

## References

- `apcplants/docs/design/parser-ir-and-multi-backend-alignment.md` §6
- `apcplants/docs/design/frontend-and-project-structure-options.md` §1, §5
- Org repository map (`.github`): planned `apc-model-ir`, `apc-tooling`
- [`docs/design/language-strategy.md`](../design/language-strategy.md)
