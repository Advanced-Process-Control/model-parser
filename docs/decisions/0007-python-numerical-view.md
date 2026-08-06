# ADR 0007: Python numerical view (`emit python`)

## Status

accepted

## Context

Python analysis and simulation workflows need executable model functions from
the same canonical IR used by the Julia views. Reimplementing equations in a
consumer would duplicate expression semantics and allow stored views to drift.

## Decision

Add a dependency-free Python codegen target, `emit python`, that emits:

- `f_<model_slug>(t, state, parameters)` when the model has no inputs, or the
  same function with a fourth `inputs` argument when inputs are declared;
- `outputs_<model_slug>` with the same arguments when output equations exist.

The RHS follows the argument order expected by SciPy ODE solvers and returns a
list of derivatives in `ir.states` declaration order. Parameters, inputs, and
outputs also follow their IR declaration order. Parameter defaults remain
documentation; callers supply numerical parameter values. Generated modules
use only the Python standard library.

Locals are evaluated sequentially in IR order. Expressions are rendered from
the explicit expression tree; `ifelse` is emitted as a helper call so all three
arguments are evaluated before selection, preserving IR semantics.

## Consequences

- **Positive:** Stored Python and Julia views share one semantic source and can
  be checked into `model-library` with deterministic hashes.
- **Positive:** Generated functions work with Python sequences and require no
  generated-code dependency on NumPy or SciPy.
- **Negative:** Callers must supply packed vectors in declaration order and
  adapt the optional input argument to their solver integration.

## Alternatives considered

1. **Generate NumPy-specific code** - rejected because scalar expressions and
   lists cover the current ODE contract without adding a runtime dependency.
2. **Return a class or simulator** - rejected because execution and scenario
   handling are outside the parser's scaffold/codegen scope.

## References

- ADR 0003 (explicit expression IR)
- ADR 0005 (CLI `emit <target>` shape)
- ADR 0006 (Julia numerical RHS view)
- `docs/design/model-parser.md` section 5 (CLI)