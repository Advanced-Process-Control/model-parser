"""Tests for the Julia / ModelingToolkit backend (IR -> .jl)."""

from model_parser.backends import emit_julia, expr_to_julia
from model_parser.frontends import parse_ini_text
from model_parser.frontends.expr_parser import parse_expression


def test_expr_rendering_roundtrip_shape():
    code = expr_to_julia(parse_expression("mu_max * S / (K_S + S)"))
    assert code == "((mu_max * S) / (K_S + S))"


def test_pow_renders_as_caret():
    assert expr_to_julia(parse_expression("pow(x, 2)")) == "(x ^ 2.0)"


def test_if_renders_as_ifelse():
    assert expr_to_julia(parse_expression("if(x > 0, x, 0)")) == "ifelse((x > 0.0), x, 0.0)"


def test_emit_targets_mtk_v11_idioms(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    code = emit_julia(ir)
    assert "using ModelingToolkit" in code
    assert "t_nounits as t, D_nounits as D" in code
    assert "System(eqs, t)" in code
    assert "mtkcompile" in code
    # MTK v11: the deprecated @mtkmodel DSL must not be used.
    assert "@mtkmodel" not in code
    # No legacy structural_simplify.
    assert "structural_simplify" not in code


def test_emit_includes_equations(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    code = emit_julia(ir)
    assert "D(x0) ~" in code
    assert "mu ~" in code
    assert "y0 ~" in code


def test_emit_passes_inputs_for_models_with_inputs():
    ini = """
[ModelInfo]
Name = withinput
[Dimensions]
num_states = 1
num_inputs = 1
num_outputs = 1
[Parameters]
k = 1.0
[StateEquationLocals]
var u := u0;
[StateEquations]
dx0 = k * u - x0
[OutputEquations]
y0 = x0
"""
    ir = parse_ini_text(ini).ir
    code = emit_julia(ir)
    assert "inputs = [u0]" in code
