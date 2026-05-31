"""Core and profile validators for the canonical IR.

Structural validation (types, required fields) is handled by Pydantic at load
time. This module adds *semantic* checks (do referenced symbols exist? are
dimensions consistent?) and *profile* checks (is this IR within a backend's
supported subset?). Validation answers "is this model acceptable?"; it is
distinct from the conformance suite, which answers "do backends agree?".

Profiles currently understood:

- ``julia-analysis`` — permissive; the full IR is allowed.
- ``realtime-cpp`` — restricted: only the deterministic operator/function subset
  and no unsupported constructs (a first-cut placeholder for the PLC target).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from model_parser.ir import (
    ALLOWED_OPS,
    Call,
    Expr,
    IRModel,
    free_symbols,
)

# Operators/functions a real-time C++ target is willing to emit deterministically.
_REALTIME_CPP_OPS: frozenset[str] = frozenset(
    {
        "+",
        "-",
        "*",
        "/",
        "^",
        "neg",
        "<",
        ">",
        "<=",
        ">=",
        "==",
        "!=",
        "max",
        "min",
        "sqrt",
        "exp",
        "log",
        "abs",
        "ifelse",
    }
)

_KNOWN_PROFILES: frozenset[str] = frozenset({"julia-analysis", "realtime-cpp"})


@dataclass(frozen=True)
class Diagnostic:
    """A single validation finding."""

    level: str  # "ERROR" | "WARN"
    code: str
    message: str


@dataclass
class ValidationReport:
    """The result of validating an IR: a list of diagnostics."""

    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.level == "ERROR"]

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.level == "WARN"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def _add(self, level: str, code: str, message: str) -> None:
        self.diagnostics.append(Diagnostic(level=level, code=code, message=message))


def _iter_ops(expr: Expr) -> list[str]:
    if isinstance(expr, Call):
        ops = [expr.op]
        for arg in expr.args:
            ops.extend(_iter_ops(arg))
        return ops
    return []


def _all_expressions(ir: IRModel) -> list[tuple[str, Expr]]:
    items: list[tuple[str, Expr]] = []
    for local in ir.locals:
        items.append((f"local {local.name}", local.expr))
    for diff in ir.equations.differential:
        items.append((f"d({diff.state})/dt", diff.rhs))
    for out in ir.equations.outputs:
        items.append((f"output {out.output}", out.rhs))
    return items


def validate_ir(ir: IRModel, *, profile: str | None = None) -> ValidationReport:
    """Validate ``ir`` semantically and, optionally, against a backend ``profile``."""
    report = ValidationReport()
    declared = ir.symbol_names()

    # Duplicate declarations.
    seen: set[str] = set()
    for group in (ir.states, ir.inputs, ir.outputs, ir.parameters, ir.locals):
        for item in group:
            if item.name in seen:
                report._add(
                    "ERROR", "duplicate-symbol", f"symbol {item.name!r} is declared more than once"
                )
            seen.add(item.name)

    # Referenced-but-undeclared symbols.
    for label, expr in _all_expressions(ir):
        for ref in sorted(free_symbols(expr)):
            if ref not in declared:
                report._add(
                    "ERROR", "undeclared-symbol", f"{label} references undeclared symbol {ref!r}"
                )
        for op in _iter_ops(expr):
            if op not in ALLOWED_OPS:
                report._add("ERROR", "unknown-op", f"{label} uses unknown operator/function {op!r}")

    # Every state needs a differential equation; outputs need output equations.
    diff_states = {d.state for d in ir.equations.differential}
    for state in ir.states:
        if state.name not in diff_states:
            report._add(
                "WARN",
                "missing-state-equation",
                f"state {state.name!r} has no differential equation",
            )
    out_defs = {o.output for o in ir.equations.outputs}
    for out in ir.outputs:
        if out.name not in out_defs:
            report._add(
                "WARN", "missing-output-equation", f"output {out.name!r} has no output equation"
            )

    # Local ordering / cyclic dependency check (locals must be resolvable in order).
    _check_local_ordering(ir, report)

    if profile is not None:
        _validate_profile(ir, profile, report)

    return report


def _check_local_ordering(ir: IRModel, report: ValidationReport) -> None:
    base = (
        {v.name for v in ir.states} | {v.name for v in ir.inputs} | {p.name for p in ir.parameters}
    )
    available = set(base)
    pending = {local.name for local in ir.locals}
    for local in ir.locals:
        deps = free_symbols(local.expr) & pending
        unresolved = {d for d in deps if d not in available and d != local.name}
        if unresolved:
            report._add(
                "WARN",
                "local-ordering",
                f"local {local.name!r} references later/cyclic locals "
                f"{sorted(unresolved)}; backends may require topological ordering",
            )
        available.add(local.name)


def _validate_profile(ir: IRModel, profile: str, report: ValidationReport) -> None:
    if profile not in _KNOWN_PROFILES:
        report._add(
            "WARN",
            "unknown-profile",
            f"profile {profile!r} is not recognized; skipping profile checks",
        )
        return
    if profile == "julia-analysis":
        return  # permissive
    if profile == "realtime-cpp":
        for label, expr in _all_expressions(ir):
            for op in _iter_ops(expr):
                if op not in _REALTIME_CPP_OPS:
                    report._add(
                        "ERROR",
                        "profile-realtime-cpp",
                        f"{label} uses {op!r}, not in the realtime-cpp subset",
                    )
