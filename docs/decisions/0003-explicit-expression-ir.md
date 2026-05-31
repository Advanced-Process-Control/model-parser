# ADR 0003 — Explicit expression IR, not string rewrites

**Status:** accepted · 2026-06-01

## Context

The prototype (`ProcessModelingJL`) bridges ExprTk to Julia by rewriting
strings: regex replacement of `pow(...)` → `(...)^(...)`, `if(...)` → `ifelse`,
then `Meta.parse`. This is a valid MVP, but string rewriting is fragile —
operator precedence, associativity, nesting, and conditional semantics are
re-derived per target. With three potential targets (Julia, C++ ExprTk, Python),
this invites three subtly different semantics: the documented "expression-language
drift" risk.

## Decision

Represent expressions as an **explicit tagged tree** in the IR, with three node
kinds: `num`, `sym`, and `call` (operators and functions uniformly keyed by
`op`). The Python frontend parses the authoring expression **once** with a real
tokenizer + precedence-climbing parser into this tree; normalization (e.g.
`pow`→`^`, `if`→`ifelse`, unary `neg`) happens at parse time. Every backend is a
**renderer** of the tree; no backend re-parses strings.

## Consequences

- + Precedence/associativity resolved once, in one place
  (`frontends/expr_parser.py`).
- + Backends are simple, total tree-walks; adding one cannot reintroduce a
  parsing bug.
- + The tree is JSON-serializable, diffable, and testable at the IR level —
  conformance fixtures pin all backends to the same tree.
- + A future C++/`realtime-cpp` backend is another renderer, not a fourth parser.
- − The IR is more verbose than a stored string (acceptable; it is machine data).
- − The supported operator/function set is explicit and must be extended
  deliberately (a feature, not a bug — it is the expression sub-language
  contract).

## Alternatives considered

- *Keep string rewrites.* Rejected: does not scale to multiple backends without
  divergence; precedence bugs are easy and silent.
- *Store the raw authoring string and re-parse per backend.* Rejected: each
  backend would need its own ExprTk-compatible parser — the exact drift we are
  avoiding.
- *Adopt an existing expression IR (e.g. MathML, SymPy srepr).* Rejected for v1:
  heavier and less aligned with the small, profile-able sub-language we need;
  revisit only if interop demands it.

## References

- `apcplants/docs/design/parser-ir-and-multi-backend-alignment.md` §3
- Org architecture risk note: "expression-language drift"
- [`docs/design/ir-specification.md`](../design/ir-specification.md) §3
