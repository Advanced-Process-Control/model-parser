"""Expression IR: a small, explicit, backend-independent expression tree.

The expression sub-language is represented as a tagged tree rather than as a
backend-specific string. This is the core of ADR 0003 (explicit expression IR):
every backend lowers from the *same* tree, so conditional and numeric semantics
are defined once instead of being re-derived per target via string rewrites.

Three node kinds exist:

- :class:`Num` — a numeric literal.
- :class:`Sym` — a reference to a declared symbol (state, input, output,
  parameter, or local).
- :class:`Call` — an operator or function applied to argument expressions. All
  arithmetic operators, comparisons, unary negation, and named functions are
  represented uniformly as calls keyed by :attr:`Call.op`.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

# Canonical operator/function names used in ``Call.op``. Frontends normalize
# authoring-format spellings (e.g. ExprTk ``pow``/``if``) into these names so the
# IR carries one vocabulary. Backends own the mapping from these names to their
# own syntax. Keep this list aligned with ``docs/design/ir-specification.md``.
ARITHMETIC_OPS: frozenset[str] = frozenset({"+", "-", "*", "/", "^"})
UNARY_OPS: frozenset[str] = frozenset({"neg"})
COMPARISON_OPS: frozenset[str] = frozenset({"<", ">", "<=", ">=", "==", "!="})
FUNCTIONS: frozenset[str] = frozenset({"max", "min", "sqrt", "exp", "log", "abs", "ifelse"})
ALLOWED_OPS: frozenset[str] = ARITHMETIC_OPS | UNARY_OPS | COMPARISON_OPS | FUNCTIONS


class Num(BaseModel):
    """A numeric literal."""

    kind: Literal["num"] = "num"
    value: float


class Sym(BaseModel):
    """A reference to a declared symbol by canonical name."""

    kind: Literal["sym"] = "sym"
    name: str


class Call(BaseModel):
    """An operator or function applied to argument expressions."""

    kind: Literal["call"] = "call"
    op: str
    args: list[Expr] = Field(default_factory=list)


Expr = Annotated[Num | Sym | Call, Field(discriminator="kind")]
"""Any expression node, discriminated on the ``kind`` tag."""

Call.model_rebuild()


def num(value: float) -> Num:
    """Construct a numeric literal node."""
    return Num(value=value)


def sym(name: str) -> Sym:
    """Construct a symbol-reference node."""
    return Sym(name=name)


def call(op: str, *args: Expr) -> Call:
    """Construct an operator/function call node."""
    return Call(op=op, args=list(args))


def free_symbols(expr: Expr) -> set[str]:
    """Return the set of symbol names referenced anywhere in ``expr``."""
    if isinstance(expr, Sym):
        return {expr.name}
    if isinstance(expr, Call):
        out: set[str] = set()
        for arg in expr.args:
            out |= free_symbols(arg)
        return out
    return set()
