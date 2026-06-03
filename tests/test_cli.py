"""CLI smoke tests using Typer's CliRunner."""

from pathlib import Path

from typer.testing import CliRunner

from model_parser.cli import app

runner = CliRunner()


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "model-parser" in result.stdout


def test_parse_then_emit_pipeline(tmp_path, monod_ini):
    ini = _write(tmp_path, "monod.ini", monod_ini)
    ir_path = tmp_path / "monod.ir.json"

    parsed = runner.invoke(app, ["parse", str(ini), "-o", str(ir_path)])
    assert parsed.exit_code == 0, parsed.output
    assert ir_path.exists()

    jl_path = tmp_path / "monod.jl"
    emitted = runner.invoke(app, ["emit", "julia", str(ir_path), "-o", str(jl_path)])
    assert emitted.exit_code == 0, emitted.output
    code = jl_path.read_text()
    assert "mtkcompile" in code

    rhs_path = tmp_path / "monod_rhs.jl"
    rhs = runner.invoke(app, ["emit", "julia-rhs", str(ir_path), "-o", str(rhs_path)])
    assert rhs.exit_code == 0, rhs.output
    rhs_code = rhs_path.read_text()
    assert "f_monod_simple!" in rhs_code


def test_validate_ok(tmp_path, monod_ini):
    ini = _write(tmp_path, "monod.ini", monod_ini)
    result = runner.invoke(app, ["validate", str(ini), "--profile", "julia-analysis"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_validate_detects_undeclared_symbol(tmp_path):
    bad = """
[ModelInfo]
Name = bad
[Dimensions]
num_states = 1
num_inputs = 0
num_outputs = 0
[StateEquations]
dx0 = ghost * x0
"""
    ini = _write(tmp_path, "bad.ini", bad)
    result = runner.invoke(app, ["validate", str(ini)])
    assert result.exit_code == 1
    assert "undeclared-symbol" in result.output


def test_schema_command():
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    assert '"$schema"' in result.stdout


def test_inspect(tmp_path, monod_ini):
    ini = _write(tmp_path, "monod.ini", monod_ini)
    result = runner.invoke(app, ["inspect", str(ini)])
    assert result.exit_code == 0
    assert "monod_simple" in result.stdout


def test_diff_same_ir_twice(tmp_path, monod_ini):
    ini = _write(tmp_path, "monod.ini", monod_ini)
    ir_path = tmp_path / "m.ir.json"
    assert runner.invoke(app, ["parse", str(ini), "-o", str(ir_path)]).exit_code == 0
    result = runner.invoke(app, ["diff", str(ir_path), str(ir_path)])
    assert result.exit_code == 0
    assert "none" in result.stdout
    assert "old hash:" in result.stdout


def test_bump_json(tmp_path, monod_ini):
    ini = _write(tmp_path, "monod.ini", monod_ini)
    ir_path = tmp_path / "m.ir.json"
    assert runner.invoke(app, ["parse", str(ini), "-o", str(ir_path)]).exit_code == 0
    result = runner.invoke(app, ["bump", str(ir_path), str(ir_path), "--json"])
    assert result.exit_code == 0
    assert '"bump": "none"' in result.stdout
