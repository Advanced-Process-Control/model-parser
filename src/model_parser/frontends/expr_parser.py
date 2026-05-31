"""Parse ExprTk-style expression strings into the canonical expression IR.

This is a small, explicit tokenizer + precedence-climbing parser. It exists
instead of regex string rewrites so that operator precedence, associativity,
and conditional semantics are defined in *one* place (ADR 0003). The output is
an :data:`model_parser.ir.expr.Expr` tree that every backend lowers from.

Supported surface (the ExprTk subset used by the authoring INI format):

- numeric literals (``1``, ``1.5``, ``1e-3``);
- identifiers (symbol references);
- binary operators ``+ - * / ^`` and unary minus;
- comparisons ``< > <= >= == !=``;
- function calls ``f(a, b, ...)``;
- the ExprTk spellings ``pow(a, b)`` and ``if(c, a, b)``, normalized to ``^``
  and ``ifelse`` respectively.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from model_parser.ir.expr import Call, Expr, Num, Sym

# ExprTk function/operator spellings that map onto canonical IR op names.
_FUNCTION_ALIASES: dict[str, str] = {"pow": "^", "if": "ifelse"}

# Binary operators: name -> (left binding power, right binding power).
# Right binding power lower than left means right-associative (used for ``^``).
_BINARY: dict[str, tuple[int, int]] = {
    "==": (10, 11),
    "!=": (10, 11),
    "<": (10, 11),
    ">": (10, 11),
    "<=": (10, 11),
    ">=": (10, 11),
    "+": (20, 21),
    "-": (20, 21),
    "*": (30, 31),
    "/": (30, 31),
    "^": (51, 50),
}

_UNARY_BP = 40

_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (?P<number>\d+\.\d+(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?|\.\d+)
      | (?P<ident>[A-Za-z_]\w*)
      | (?P<op><=|>=|==|!=|[-+*/^<>(),])
    )
    """,
    re.VERBOSE,
)


class ExprParseError(ValueError):
    """Raised when an expression string cannot be parsed."""


@dataclass(frozen=True)
class _Token:
    kind: str  # "number" | "ident" | "op" | "end"
    text: str
    pos: int


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    pos = 0
    n = len(source)
    while pos < n:
        if source[pos].isspace():
            pos += 1
            continue
        match = _TOKEN_RE.match(source, pos)
        if match is None or match.start() == match.end():
            raise ExprParseError(
                f"unexpected character {source[pos]!r} at position {pos} in {source!r}"
            )
        kind = match.lastgroup
        assert kind is not None
        text = match.group(kind)
        tokens.append(_Token(kind=kind, text=text, pos=match.start(kind)))
        pos = match.end()
    tokens.append(_Token(kind="end", text="", pos=n))
    return tokens


class _Parser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens = _tokenize(source)
        self.index = 0

    @property
    def current(self) -> _Token:
        return self.tokens[self.index]

    def advance(self) -> _Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def expect_op(self, text: str) -> None:
        token = self.current
        if token.kind != "op" or token.text != text:
            raise ExprParseError(
                f"expected {text!r} but found {token.text!r} at position "
                f"{token.pos} in {self.source!r}"
            )
        self.advance()

    def parse(self) -> Expr:
        expr = self._parse_expr(0)
        if self.current.kind != "end":
            raise ExprParseError(
                f"unexpected trailing token {self.current.text!r} at position "
                f"{self.current.pos} in {self.source!r}"
            )
        return expr

    def _parse_expr(self, min_bp: int) -> Expr:
        left = self._parse_prefix()
        while True:
            token = self.current
            if token.kind != "op" or token.text not in _BINARY:
                break
            left_bp, right_bp = _BINARY[token.text]
            if left_bp < min_bp:
                break
            self.advance()
            right = self._parse_expr(right_bp)
            left = Call(op=token.text, args=[left, right])
        return left

    def _parse_prefix(self) -> Expr:
        token = self.current
        if token.kind == "op" and token.text == "-":
            self.advance()
            operand = self._parse_expr(_UNARY_BP)
            return Call(op="neg", args=[operand])
        if token.kind == "op" and token.text == "+":
            self.advance()
            return self._parse_expr(_UNARY_BP)
        if token.kind == "op" and token.text == "(":
            self.advance()
            inner = self._parse_expr(0)
            self.expect_op(")")
            return inner
        if token.kind == "number":
            self.advance()
            return Num(value=float(token.text))
        if token.kind == "ident":
            self.advance()
            if self.current.kind == "op" and self.current.text == "(":
                return self._parse_call(token.text)
            return Sym(name=token.text)
        raise ExprParseError(
            f"unexpected token {token.text!r} at position {token.pos} in {self.source!r}"
        )

    def _parse_call(self, name: str) -> Expr:
        self.expect_op("(")
        args: list[Expr] = []
        if not (self.current.kind == "op" and self.current.text == ")"):
            args.append(self._parse_expr(0))
            while self.current.kind == "op" and self.current.text == ",":
                self.advance()
                args.append(self._parse_expr(0))
        self.expect_op(")")
        op = _FUNCTION_ALIASES.get(name, name)
        return Call(op=op, args=args)


def parse_expression(source: str) -> Expr:
    """Parse a single ExprTk-style expression string into an IR expression tree."""
    text = source.strip().rstrip(";").strip()
    if not text:
        raise ExprParseError("empty expression")
    return _Parser(text).parse()
