"""Command-line interface for model-parser.

The CLI exposes the IR transformations as composable subcommands. The two core
verbs follow the ecosystem's transformation vocabulary:

    model-parser parse  <model.ini>      # authoring format  -> canonical IR JSON
    model-parser emit julia <model.ir.json>  # canonical IR  -> MTK Julia script

Plus supporting commands: ``validate``, ``inspect``, ``ast``, and ``schema``.

Exit codes:
    0  success, no ERROR-level diagnostics
    1  at least one ERROR diagnostic during execution
    2  invalid usage / load failure before meaningful work
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from model_parser import __version__
from model_parser.backends import emit_julia
from model_parser.frontends import parse_ini_file
from model_parser.io import dumps_ir, load_ir, save_ir, with_content_hash
from model_parser.schema import dumps_schema
from model_parser.semantic_diff import compare_ir, result_to_jsonable
from model_parser.validation import validate_ir

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Convert process-model definitions to and from a canonical IR.",
)
emit_app = typer.Typer(no_args_is_help=True, help="Lower the canonical IR into a target view.")
app.add_typer(emit_app, name="emit")

_err = typer.style("error:", fg=typer.colors.RED, bold=True)
_warn = typer.style("warning:", fg=typer.colors.YELLOW, bold=True)


def _echo_err(message: str) -> None:
    typer.echo(f"{_err} {message}", err=True)


def _echo_warn(message: str) -> None:
    typer.echo(f"{_warn} {message}", err=True)


@app.callback(invoke_without_command=True)
def _main(
    version: bool = typer.Option(
        False, "--version", help="Show the version and exit.", is_eager=True
    ),
) -> None:
    if version:
        typer.echo(f"model-parser {__version__}")
        raise typer.Exit()


@app.command()
def parse(
    source: Path = typer.Argument(..., exists=True, readable=True, help="Authoring file."),
    output: Path | None = typer.Option(
        None, "-o", "--output", help="IR JSON output path (default: stdout)."
    ),
    from_format: str = typer.Option(
        "exprtk-ini", "--from", help="Authoring format of the source file."
    ),
) -> None:
    """Parse an authoring file (default: ExprTk INI) into canonical IR JSON."""
    if from_format != "exprtk-ini":
        _echo_err(f"unsupported source format {from_format!r} (only 'exprtk-ini' for now)")
        raise typer.Exit(code=2)

    result = parse_ini_file(str(source))
    ir = with_content_hash(result.ir)
    for warning in result.warnings:
        _echo_warn(warning)

    if output is None:
        typer.echo(dumps_ir(ir), nl=False)
    else:
        save_ir(ir, output)
        typer.echo(f"wrote IR to {output}", err=True)


@emit_app.command("julia")
def emit_julia_cmd(
    ir_file: Path = typer.Argument(..., exists=True, readable=True, help="IR JSON file."),
    output: Path | None = typer.Option(
        None, "-o", "--output", help="Julia output path (default: stdout)."
    ),
) -> None:
    """Generate a ModelingToolkit (v11) Julia script from an IR file."""
    ir = load_ir(ir_file)
    code = emit_julia(ir)
    if output is None:
        typer.echo(code, nl=False)
    else:
        Path(output).write_text(code, encoding="utf-8")
        typer.echo(f"wrote Julia model to {output}", err=True)


@app.command()
def diff(
    old_ir: Path = typer.Argument(
        ..., exists=True, readable=True, help="Baseline IR JSON (e.g. last release)."
    ),
    new_ir: Path = typer.Argument(
        ..., exists=True, readable=True, help="Candidate IR JSON (e.g. after edits)."
    ),
    json_out: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Compare two canonical IR files and list semantic differences."""
    old = load_ir(old_ir)
    new = load_ir(new_ir)
    result = compare_ir(old, new)
    if json_out:
        typer.echo(json.dumps(result_to_jsonable(result), indent=2))
        return
    typer.echo(f"old hash: {result.old_hash}")
    typer.echo(f"new hash: {result.new_hash}")
    typer.echo(f"suggested bump: {result.bump.value}")
    if not result.items:
        typer.echo("no classified differences (semantic bodies match)")
        return
    for item in result.items:
        typer.echo(f"  [{item.code}] {item.message}")


@app.command()
def bump(
    old_ir: Path = typer.Argument(
        ..., exists=True, readable=True, help="Baseline IR JSON (e.g. last release)."
    ),
    new_ir: Path = typer.Argument(
        ..., exists=True, readable=True, help="Candidate IR JSON (e.g. after edits)."
    ),
    json_out: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Suggest a SemVer bump by comparing two canonical IR files (advisory)."""
    old = load_ir(old_ir)
    new = load_ir(new_ir)
    result = compare_ir(old, new)
    if json_out:
        typer.echo(json.dumps(result_to_jsonable(result), indent=2))
        return
    typer.echo(result.bump.value)
    if result.items:
        for item in result.items:
            typer.echo(f"{item.code}: {item.message}", err=True)


@app.command()
def validate(
    target: Path = typer.Argument(..., exists=True, readable=True, help="IR JSON or INI file."),
    profile: str | None = typer.Option(
        None, "--profile", help="Backend profile to check (e.g. julia-analysis, realtime-cpp)."
    ),
) -> None:
    """Validate an IR (or an INI parsed on the fly) and report diagnostics."""
    ir = _load_any(target)
    report = validate_ir(ir, profile=profile)
    for diag in report.diagnostics:
        prefix = _err if diag.level == "ERROR" else _warn
        typer.echo(f"{prefix} [{diag.code}] {diag.message}", err=True)
    if report.ok:
        typer.echo(f"OK: {ir.model.name} valid" + (f" for profile {profile!r}" if profile else ""))
    else:
        typer.echo(f"FAILED: {len(report.errors)} error(s)", err=True)
        raise typer.Exit(code=1)


@app.command()
def inspect(
    target: Path = typer.Argument(..., exists=True, readable=True, help="IR JSON or INI file."),
) -> None:
    """Print a human-readable summary of a model."""
    ir = _load_any(target)
    typer.echo(f"model:       {ir.model.name}")
    if ir.model.description:
        typer.echo(f"description: {ir.model.description}")
    typer.echo(f"ir version:  {ir.ir_version}")
    typer.echo(f"states:      {len(ir.states)}  ({', '.join(v.name for v in ir.states)})")
    typer.echo(f"inputs:      {len(ir.inputs)}  ({', '.join(v.name for v in ir.inputs)})")
    typer.echo(f"outputs:     {len(ir.outputs)}  ({', '.join(v.name for v in ir.outputs)})")
    typer.echo(f"parameters:  {len(ir.parameters)}")
    typer.echo(f"locals:      {len(ir.locals)}")
    typer.echo(f"profiles:    {', '.join(ir.profiles)}")
    if ir.provenance and ir.provenance.content_hash:
        typer.echo(f"hash:        {ir.provenance.content_hash}")


@app.command()
def ast(
    source: Path = typer.Argument(..., exists=True, readable=True, help="ExprTk INI file."),
    output: Path | None = typer.Option(
        None, "-o", "--output", help="AST/IR debug JSON output path (default: stdout)."
    ),
) -> None:
    """Export the parsed IR as a debug JSON tree (parser inspection)."""
    result = parse_ini_file(str(source))
    text = dumps_ir(result.ir)
    if output is None:
        typer.echo(text, nl=False)
    else:
        Path(output).write_text(text, encoding="utf-8")
        typer.echo(f"wrote debug tree to {output}", err=True)


@app.command()
def schema(
    output: Path | None = typer.Option(
        None, "-o", "--output", help="JSON Schema output path (default: stdout)."
    ),
) -> None:
    """Print or write the canonical IR JSON Schema."""
    text = dumps_schema()
    if output is None:
        typer.echo(text, nl=False)
    else:
        Path(output).write_text(text, encoding="utf-8")
        typer.echo(f"wrote schema to {output}", err=True)


def _load_any(path: Path):
    """Load an IR from a ``.json`` file, or parse an INI file on the fly."""
    if path.suffix.lower() == ".json":
        return load_ir(path)
    return parse_ini_file(str(path)).ir


def run() -> None:
    """Entry point wrapper that maps uncaught errors to exit code 2."""
    try:
        app()
    except (ValueError, FileNotFoundError) as exc:  # parse/codegen errors
        _echo_err(str(exc))
        sys.exit(2)


if __name__ == "__main__":
    run()
