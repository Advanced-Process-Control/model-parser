# TODO: Conformance fixtures and cross-language parity

## Goal

Grow **shared IR fixtures** with **expected Julia codegen** (and later
**expected trajectories** or numerical checks), executed in **Python** and
**Julia** (`ModelParserJL`) so the two runtimes cannot drift silently.

## Why

- [`docs/design/language-strategy.md`](../design/language-strategy.md): the IR
  file is the boundary; parity tests are the enforcement mechanism.
- Reduces regression risk whenever MTK idioms or codegen change (see ADR 0004).

## Scope hints

- Start with golden `.jl` snippets or full files under `tests/` or `examples/`.
- Julia side: documented `Pkg.test` or script in CI (may remain optional job
  until Julia CI is wired).

## References

- [`docs/design/model-parser.md`](../design/model-parser.md) roadmap §2.
- [ADR 0001](../decisions/0001-python-cli-with-julia-backend.md), [ADR 0004](../decisions/0004-target-mtk-v11-idioms.md).

## Acceptance sketch

- At least N≥2 fixtures with checked `emit julia` output.
- Document how to refresh goldens when codegen intentionally changes.
