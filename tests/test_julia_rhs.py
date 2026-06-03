"""Tests for the Julia numerical RHS backend (IR -> f! / outputs!)."""

import pytest

from model_parser.backends import emit_julia_rhs
from model_parser.backends.julia_expr import JuliaCodegenError
from model_parser.frontends import parse_ini_text


def test_emit_rhs_monod(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    code = emit_julia_rhs(ir)
    assert "function f_monod_simple!(du, u, p, t)" in code
    assert "mu_max, K_S, Y_XS = p[1], p[2], p[3]" in code
    assert "du[1] =" in code and "du[2] =" in code
    assert "function outputs_monod_simple!(y, u, p, t)" in code
    assert "y[1] =" in code and "y[2] =" in code
    assert "using ModelingToolkit" not in code


def test_emit_rhs_with_inputs():
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
    code = emit_julia_rhs(ir)
    assert "function f_withinput!(du, u, p, t, inp)" in code
    assert "u0 = inp[1]" in code
    assert "function outputs_withinput!(y, u, p, t, inp)" in code


def test_emit_rhs_rejects_unknown_diff_state():
    ini = """
[ModelInfo]
Name = bad
[Dimensions]
num_states = 1
num_inputs = 0
num_outputs = 0
[StateEquations]
dx99 = 0.0
"""
    ir = parse_ini_text(ini).ir
    with pytest.raises(JuliaCodegenError, match="x99"):
        emit_julia_rhs(ir)
