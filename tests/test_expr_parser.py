"""Tests for the ExprTk expression parser."""

import pytest

from model_parser.frontends.expr_parser import ExprParseError, parse_expression
from model_parser.ir import Call, Num, Sym


def test_parses_number():
    assert parse_expression("1.5e-3") == Num(value=1.5e-3)


def test_parses_symbol():
    assert parse_expression("mu_max") == Sym(name="mu_max")


def test_precedence_and_associativity():
    # a + b * c  ->  a + (b * c)
    expr = parse_expression("a + b * c")
    assert isinstance(expr, Call) and expr.op == "+"
    assert isinstance(expr.args[1], Call) and expr.args[1].op == "*"


def test_power_is_right_associative():
    # 2 ^ 3 ^ 2  ->  2 ^ (3 ^ 2)
    expr = parse_expression("2 ^ 3 ^ 2")
    assert expr.op == "^"
    assert isinstance(expr.args[1], Call) and expr.args[1].op == "^"


def test_unary_minus():
    expr = parse_expression("-x")
    assert expr.op == "neg" and expr.args[0] == Sym(name="x")


def test_pow_alias_maps_to_caret():
    expr = parse_expression("pow(x, 2)")
    assert expr.op == "^"
    assert expr.args == [Sym(name="x"), Num(value=2.0)]


def test_if_alias_maps_to_ifelse():
    expr = parse_expression("if(x > 0, x, 0)")
    assert expr.op == "ifelse"
    assert expr.args[0].op == ">"


def test_monod_local():
    expr = parse_expression("mu_max * S / (K_S + S)")
    assert expr.op == "/"


def test_nested_functions():
    expr = parse_expression("max(min(a, b), 0)")
    assert expr.op == "max"
    assert expr.args[0].op == "min"


def test_rejects_trailing_garbage():
    with pytest.raises(ExprParseError):
        parse_expression("a + )")


def test_rejects_empty():
    with pytest.raises(ExprParseError):
        parse_expression("   ")
