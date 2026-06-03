# ADR 0006: Julia numerical RHS view (`emit julia-rhs`)

## Status

accepted

## Context

Some analysis workflows (explicit vector ODEs, custom sensitivity tooling, or
bridges that do not use ModelingToolkit) need a **plain in-place RHS**
`f!(du, u, p, t)` with stable symbol-to-index packing, while the ecosystem
standard remains an MTK-generated `System` from the same IR.

## Decision

Add a second Julia **codegen** target, `emit julia-rhs`, that lowers the same
canonical IR to:

- `f_<model_slug>!(du, u, p, t)` when the scaffold has no inputs, or
  `f_<model_slug>!(du, u, p, t, inp)` when it has inputs (`inp` order = IR inputs
  list order);
- `outputs_<model_slug>!(y, u, p, t)` (same optional `inp`) when the IR
  carries output equations.

Packing rules: `u` and `du` follow `ir.states` order; `p` follows `ir.parameters`
order (defaults in the IR are **not** applied inside `f!` — callers supply
numeric `p`). Locals are emitted as sequential assignments in IR order, aligned
with the MTK lowering order.

Expression rendering is shared with the MTK backend via `julia_expr.py` so
semantics are not duplicated.

## Consequences

- **Positive:** One IR, two diffable Julia views; numerical and symbolic stacks
  stay aligned.
- **Negative:** Callers must respect documented packing; no automatic wiring to
  MTK `ODEProblem` from the RHS view alone.

## Alternatives considered

1. **Generate RHS only in downstream repos** — rejected: duplicates expression
   semantics and drifts from the IR contract.
2. **Single `emit julia` with a flag** — rejected: CLI stays clearer with
   separate targets (`emit cpp`, etc.) per ADR 0005.

## References

- ADR 0002 (codegen over serialized `System`)
- ADR 0003 (explicit expression IR)
- ADR 0005 (CLI `emit <target>` shape)
- `docs/design/model-parser.md` §5 (CLI)
