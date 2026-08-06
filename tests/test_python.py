"""Tests for the Python numerical backend."""

import pytest

from model_parser.backends import PythonCodegenError, emit_python
from model_parser.frontends import parse_ini_text


def _execute(code: str) -> dict[str, object]:
    namespace: dict[str, object] = {}
    exec(compile(code, "<generated-model>", "exec"), namespace)
    return namespace


def test_emit_python_monod_executes(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    code = emit_python(ir)
    namespace = _execute(code)

    rhs = namespace["f_monod_simple"]
    outputs = namespace["outputs_monod_simple"]
    parameters = [0.4, 0.01, 0.5]

    assert rhs(0.0, [0.05, 15.0], parameters) == pytest.approx(
        [0.01998667554963358, -0.03997335109926716]
    )
    assert outputs(0.0, [0.05, 15.0], parameters) == pytest.approx([0.05, 0.3997335109926716])


def test_emit_python_with_inputs_executes():
    ini = """
[ModelInfo]
Name = withinput
[Dimensions]
num_states = 1
num_inputs = 1
num_outputs = 1
[Parameters]
k = 2.0
[StateEquations]
dx0 = k * u0 - x0
[OutputEquations]
y0 = x0
"""
    namespace = _execute(emit_python(parse_ini_text(ini).ir))

    assert namespace["f_withinput"](0.0, [3.0], [2.0], [4.0]) == [5.0]
    assert namespace["outputs_withinput"](0.0, [3.0], [2.0], [4.0]) == [3.0]


def test_emit_python_functions_and_conditionals_execute():
    ini = """
[ModelInfo]
Name = functions
[Dimensions]
num_states = 1
num_inputs = 0
num_outputs = 0
[StateEquations]
dx0 = if(x0 > 0, sqrt(x0 ^ 2) + exp(0), log(1) + abs(-1))
"""
    namespace = _execute(emit_python(parse_ini_text(ini).ir))

    assert namespace["f_functions"](0.0, [2.0], []) == pytest.approx([3.0])
    assert namespace["f_functions"](0.0, [-2.0], []) == pytest.approx([1.0])


def test_emit_python_rejects_runtime_name_collision():
    ini = """
[ModelInfo]
Name = collision
[Dimensions]
num_states = 1
num_inputs = 0
num_outputs = 0
[Parameters]
state = 1.0
[StateEquations]
dx0 = state * x0
"""
    ir = parse_ini_text(ini).ir
    with pytest.raises(PythonCodegenError, match="generated Python runtime"):
        emit_python(ir)


def test_emit_python_rejects_unknown_diff_state():
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
    with pytest.raises(PythonCodegenError, match="x99"):
        emit_python(ir)
