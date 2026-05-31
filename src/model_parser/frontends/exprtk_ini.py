"""ExprTk INI frontend: parse an INI-style model file into the canonical IR.

This implements the ``parse`` + ``normalize`` transformations for the INI
authoring format used by the existing MPC / simulation toolchain. The grammar is
section-oriented:

- ``[ModelInfo]``        — ``Name``, ``Description``, ``Version`` key/values.
- ``[Dimensions]``       — ``num_states``, ``num_inputs``, ``num_outputs``.
- ``[Parameters]``       — ``name = value`` with optional trailing ``; comment``.
- ``[StateEquationLocals]`` — ``var name := expr;`` intermediate expressions.
- ``[StateEquations]``   — ``dxN = expr`` differential equations.
- ``[OutputEquations]``  — ``yN = expr`` plus inline ``name := expr`` locals.
- ``[x0]`` / ``[u0]``    — initial values. **Dropped from the scaffold** with a
  warning: initial values belong to a scenario, not the model scaffold
  (org contracts §3). They bootstrap simulation but are not IR semantics.

States are named ``x0..x{n-1}``, inputs ``u0..``, and outputs ``y0..`` to match
the authoring convention; locals keep their authored names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from model_parser.frontends.expr_parser import parse_expression
from model_parser.ir import (
    DiffEq,
    Equations,
    IRModel,
    Local,
    ModelInfo,
    OutputEq,
    Parameter,
    Provenance,
    Variable,
)

SOURCE_FORMAT = "exprtk-ini"

_SECTION_RE = re.compile(r"^\[(.+)\]$")
_KV_RE = re.compile(r"^(\S+)\s*=\s*(.+)$")
_LOCAL_RE = re.compile(r"^(?:var\s+)?(\w+)\s*:=\s*(.+)$")
_DIFF_RE = re.compile(r"^dx(\d+)\s*=\s*(.+)$")
_OUTPUT_RE = re.compile(r"^y(\d+)\s*=\s*(.+)$")


class IniParseError(ValueError):
    """Raised when an INI model file cannot be parsed."""


@dataclass
class ParseResult:
    """The outcome of parsing an authoring file: the IR plus diagnostics."""

    ir: IRModel
    warnings: list[str] = field(default_factory=list)


def _strip_comment(line: str) -> str:
    """Strip a trailing ``; ...`` comment / statement terminator from a line.

    A leading ``;`` means the whole line is a comment. Otherwise everything from
    the first ``;`` (statement terminator or comment) onward is removed; the
    authoring format never embeds ``;`` inside an expression.
    """
    stripped = line.strip()
    if not stripped or stripped[0] == ";":
        return ""
    idx = stripped.find(";")
    return stripped if idx < 0 else stripped[:idx].strip()


def parse_ini_sections(text: str) -> dict[str, list[str]]:
    """Split INI text into a mapping of section name -> content lines."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line:
            continue
        match = _SECTION_RE.match(line)
        if match is not None:
            current = match.group(1)
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return sections


def _parse_kv(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines:
        match = _KV_RE.match(line)
        if match is not None:
            result[match.group(1)] = match.group(2).strip()
    return result


def parse_ini_text(text: str, *, source_file: str | None = None) -> ParseResult:
    """Parse INI model text into an :class:`IRModel` with diagnostics."""
    sections = parse_ini_sections(text)
    warnings: list[str] = []

    info = _parse_kv(sections.get("ModelInfo", []))
    dims = _parse_kv(sections.get("Dimensions", []))

    def _dim(key: str) -> int:
        if key not in dims:
            raise IniParseError(f"[Dimensions] missing required key {key!r}")
        return int(dims[key])

    n_states = _dim("num_states")
    n_inputs = _dim("num_inputs")
    n_outputs = _dim("num_outputs")

    states = [Variable(name=f"x{i}") for i in range(n_states)]
    inputs = [Variable(name=f"u{i}") for i in range(n_inputs)]
    outputs = [Variable(name=f"y{i}") for i in range(n_outputs)]

    parameters: list[Parameter] = []
    for line in sections.get("Parameters", []):
        match = _KV_RE.match(line)
        if match is None:
            warnings.append(f"ignored unparsable parameter line: {line!r}")
            continue
        parameters.append(Parameter(name=match.group(1), default=float(match.group(2).strip())))

    locals_list: list[Local] = []
    for line in sections.get("StateEquationLocals", []):
        match = _LOCAL_RE.match(line)
        if match is None:
            raise IniParseError(f"cannot parse local line: {line!r}")
        locals_list.append(Local(name=match.group(1), expr=parse_expression(match.group(2))))

    differential: list[DiffEq] = []
    for line in sections.get("StateEquations", []):
        match = _DIFF_RE.match(line)
        if match is None:
            warnings.append(f"ignored unparsable state equation: {line!r}")
            continue
        idx = int(match.group(1))
        differential.append(DiffEq(state=f"x{idx}", rhs=parse_expression(match.group(2))))

    output_eqs: list[OutputEq] = []
    for line in sections.get("OutputEquations", []):
        out_match = _OUTPUT_RE.match(line)
        if out_match is not None:
            idx = int(out_match.group(1))
            output_eqs.append(OutputEq(output=f"y{idx}", rhs=parse_expression(out_match.group(2))))
            continue
        local_match = _LOCAL_RE.match(line)
        if local_match is not None:
            locals_list.append(
                Local(
                    name=local_match.group(1),
                    expr=parse_expression(local_match.group(2)),
                )
            )
            continue
        warnings.append(f"ignored unparsable output line: {line!r}")

    for section in ("x0", "u0"):
        if sections.get(section):
            warnings.append(
                f"dropped [{section}] initial values from the scaffold: initial "
                "values belong to a scenario, not the model IR"
            )

    ir = IRModel(
        model=ModelInfo(
            name=info.get("Name", "unnamed_model"),
            description=info.get("Description"),
            source_version=info.get("Version"),
        ),
        parameters=parameters,
        states=states,
        inputs=inputs,
        outputs=outputs,
        locals=locals_list,
        equations=Equations(differential=differential, outputs=output_eqs),
        provenance=Provenance(
            tool=_tool_id(),
            created_at=datetime.now(UTC).isoformat(),
            source_format=SOURCE_FORMAT,
            source_file=source_file,
        ),
    )
    return ParseResult(ir=ir, warnings=warnings)


def parse_ini_file(path: str) -> ParseResult:
    """Parse an INI model file from disk into an :class:`IRModel`."""
    from pathlib import Path

    text = Path(path).read_text(encoding="utf-8")
    return parse_ini_text(text, source_file=str(path))


def _tool_id() -> str:
    from model_parser import __version__

    return f"model-parser@{__version__}"
