"""Tests for the ExprTk INI frontend (INI -> canonical IR)."""

from model_parser.frontends import parse_ini_text
from model_parser.validation import validate_ir


def test_parses_dimensions_and_names(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    assert ir.model.name == "monod_simple"
    assert [v.name for v in ir.states] == ["x0", "x1"]
    assert [v.name for v in ir.outputs] == ["y0", "y1"]
    assert ir.inputs == []


def test_parameters_with_defaults(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    params = {p.name: p.default for p in ir.parameters}
    assert params == {"mu_max": 0.4, "K_S": 0.01, "Y_XS": 0.5}


def test_locals_and_equations(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    assert [local.name for local in ir.locals] == ["X", "S", "mu"]
    assert [d.state for d in ir.equations.differential] == ["x0", "x1"]
    assert [o.output for o in ir.equations.outputs] == ["y0", "y1"]


def test_initial_values_are_dropped_with_warning(monod_ini):
    result = parse_ini_text(monod_ini)
    assert any("x0" in w for w in result.warnings)


def test_parsed_ir_validates(monod_ini):
    ir = parse_ini_text(monod_ini).ir
    report = validate_ir(ir, profile="julia-analysis")
    assert report.ok, report.errors
