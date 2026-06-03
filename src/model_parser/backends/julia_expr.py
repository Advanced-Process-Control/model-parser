"""Shared Julia expression lowering from the IR expression tree.

Used by multiple Julia codegen backends so expression semantics stay in one
place (see ADR 0003).
"""

from __future__ import annotations

from model_parser.ir import Call, Expr, IRModel, Num, Sym

# IR op name -> Julia infix operator.
_INFIX: dict[str, str] = {
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "^": "^",
    "==": "==",
    "!=": "!=",
    "<": "<",
    ">": ">",
    "<=": "<=",
    ">=": ">=",
}

# IR op name -> Julia function name.
_FUNCS: dict[str, str] = {
    "max": "max",
    "min": "min",
    "sqrt": "sqrt",
    "exp": "exp",
    "log": "log",
    "abs": "abs",
    "ifelse": "ifelse",
}


class JuliaCodegenError(ValueError):
    """Raised when an IR construct cannot be lowered to Julia."""


def julia_model_slug(ir: IRModel) -> str:
    """Return a safe Julia identifier fragment derived from ``ir.model.name``."""
    name = ir.model.name or "model"
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    if not cleaned or not (cleaned[0].isalpha() or cleaned[0] == "_"):
        cleaned = f"m_{cleaned}"
    return cleaned


def julia_number_literal(value: float) -> str:
    """Format a floating IR literal as Julia source text."""
    if value.is_integer():
        return f"{value:.1f}"
    return repr(value)


def expr_to_julia(expr: Expr) -> str:
    """Render an IR expression as a parenthesized Julia expression string."""
    if isinstance(expr, Num):
        return julia_number_literal(expr.value)
    if isinstance(expr, Sym):
        return expr.name
    if isinstance(expr, Call):
        return _render_call(expr)
    raise JuliaCodegenError(f"unknown expression node: {expr!r}")


def _render_call(call: Call) -> str:
    op = call.op
    args = call.args
    if op == "neg":
        if len(args) != 1:
            raise JuliaCodegenError("'neg' expects exactly one argument")
        return f"(-{expr_to_julia(args[0])})"
    if op in _INFIX:
        if len(args) != 2:
            raise JuliaCodegenError(f"operator {op!r} expects two arguments")
        left, right = (expr_to_julia(a) for a in args)
        return f"({left} {_INFIX[op]} {right})"
    if op in _FUNCS:
        rendered = ", ".join(expr_to_julia(a) for a in args)
        return f"{_FUNCS[op]}({rendered})"
    raise JuliaCodegenError(f"unsupported operator/function {op!r}")
