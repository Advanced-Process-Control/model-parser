"""Semantic comparison of two canonical IR models.

Used by the ``diff`` and ``bump`` CLI commands to support versioned model
libraries. Bump suggestions are **advisory** and conservative: when in doubt,
prefer ``major`` over a false compatibility guarantee.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from model_parser.io import compute_content_hash
from model_parser.ir import IRModel, Variable


class BumpLevel(StrEnum):
    """Suggested SemVer bump for the *model* (not ``ir_version``)."""

    NONE = "none"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


@dataclass(frozen=True)
class DiffItem:
    """One detected difference between two IRs."""

    code: str
    message: str


@dataclass
class SemanticDiffResult:
    """Outcome of comparing two IR models."""

    old_hash: str
    new_hash: str
    bump: BumpLevel
    items: list[DiffItem] = field(default_factory=list)


def _expr_json(expr: Any) -> str:
    """Stable JSON for an expression subtree (Pydantic model or dict)."""
    if hasattr(expr, "model_dump"):
        data = expr.model_dump(mode="json")
    else:
        data = expr
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _metadata_equal(a: dict[str, str], b: dict[str, str]) -> bool:
    return sorted(a.items()) == sorted(b.items())


def _variable_cosmetic_equal(old: Variable, new: Variable) -> bool:
    return old.unit == new.unit and old.description == new.description and old.roles == new.roles


def compare_ir(old: IRModel, new: IRModel) -> SemanticDiffResult:
    """Compare two IR models and suggest a SemVer bump level.

    Args:
        old: Baseline IR (e.g. last released revision).
        new: Candidate IR (e.g. after editing authoring files).

    Returns:
        A :class:`SemanticDiffResult` with hashes, bump level, and human messages.
    """
    old_hash = compute_content_hash(old)
    new_hash = compute_content_hash(new)
    items: list[DiffItem] = []

    if old_hash == new_hash:
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.NONE, items=[]
        )

    if old.model.name != new.model.name:
        items.append(
            DiffItem(
                "model-name",
                f"model name changed: {old.model.name!r} -> {new.model.name!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    if old.ir_version != new.ir_version:
        items.append(
            DiffItem(
                "ir-version",
                f"ir_version changed: {old.ir_version!r} -> {new.ir_version!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    if old.independent_variable != new.independent_variable:
        items.append(
            DiffItem(
                "independent-variable",
                "independent_variable changed: "
                f"{old.independent_variable!r} -> {new.independent_variable!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    old_state_names = [s.name for s in old.states]
    new_state_names = [s.name for s in new.states]
    if old_state_names != new_state_names:
        items.append(
            DiffItem(
                "states",
                f"state declarations changed: {old_state_names!r} -> {new_state_names!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    old_input_names = [s.name for s in old.inputs]
    new_input_names = [s.name for s in new.inputs]
    if old_input_names != new_input_names:
        items.append(
            DiffItem(
                "inputs",
                f"input declarations changed: {old_input_names!r} -> {new_input_names!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    old_output_names = [s.name for s in old.outputs]
    new_output_names = [s.name for s in new.outputs]
    if old_output_names != new_output_names:
        items.append(
            DiffItem(
                "outputs",
                f"output declarations changed: {old_output_names!r} -> {new_output_names!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    old_locals = {loc.name: loc for loc in old.locals}
    new_locals = {loc.name: loc for loc in new.locals}
    if set(old_locals) != set(new_locals):
        items.append(
            DiffItem(
                "locals",
                f"local names changed: {sorted(old_locals)!r} -> {sorted(new_locals)!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )
    for name in sorted(old_locals):
        if _expr_json(old_locals[name].expr) != _expr_json(new_locals[name].expr):
            items.append(DiffItem("local-expr", f"expression for local {name!r} changed"))
            return SemanticDiffResult(
                old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
            )

    old_diff = {d.state: d for d in old.equations.differential}
    new_diff = {d.state: d for d in new.equations.differential}
    if set(old_diff) != set(new_diff):
        items.append(DiffItem("differential", "differential equation states changed"))
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )
    for state in sorted(old_diff):
        if _expr_json(old_diff[state].rhs) != _expr_json(new_diff[state].rhs):
            items.append(DiffItem("differential-expr", f"rhs for state {state!r} changed"))
            return SemanticDiffResult(
                old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
            )

    old_out = {o.output: o for o in old.equations.outputs}
    new_out = {o.output: o for o in new.equations.outputs}
    if set(old_out) != set(new_out):
        items.append(DiffItem("outputs-eq", "output equation targets changed"))
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )
    for out in sorted(old_out):
        if _expr_json(old_out[out].rhs) != _expr_json(new_out[out].rhs):
            items.append(DiffItem("output-expr", f"rhs for output {out!r} changed"))
            return SemanticDiffResult(
                old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
            )

    old_params = list(old.parameters)
    new_params = list(new.parameters)
    old_names = [p.name for p in old_params]
    new_names = [p.name for p in new_params]

    if old_names == new_names:
        defaults_changed = any(
            old_params[i].default != new_params[i].default for i in range(len(old_params))
        )
        if defaults_changed:
            items.append(DiffItem("parameter-defaults", "one or more parameter defaults changed"))
            bump = BumpLevel.PATCH
        else:
            bump = BumpLevel.NONE
    elif len(new_names) > len(old_names) and new_names[: len(old_names)] == old_names:
        prefix_ok = True
        for i, _name in enumerate(old_names):
            if (
                old_params[i].name != new_params[i].name
                or old_params[i].default != new_params[i].default
            ):
                prefix_ok = False
                break
        if prefix_ok:
            added = new_names[len(old_names) :]
            items.append(
                DiffItem(
                    "parameters-added",
                    f"parameters appended (additive): {added!r}",
                )
            )
            bump = BumpLevel.MINOR
        else:
            items.append(
                DiffItem(
                    "parameters",
                    "parameter list changed in a non-additive way",
                )
            )
            return SemanticDiffResult(
                old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
            )
    else:
        items.append(
            DiffItem(
                "parameters",
                f"parameter names changed: {old_names!r} -> {new_names!r}",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    for i in range(len(old_names)):
        o_p, n_p = old_params[i], new_params[i]
        if o_p.unit != n_p.unit or o_p.description != n_p.description:
            items.append(
                DiffItem(
                    "parameter-metadata",
                    f"parameter {o_p.name!r}: unit or description changed",
                )
            )
            bump = _raise_bump(bump, BumpLevel.PATCH)

    for name in sorted(old_locals):
        ol, nl = old_locals[name], new_locals[name]
        if ol.unit != nl.unit or ol.description != nl.description:
            items.append(
                DiffItem(
                    "local-metadata",
                    f"local {name!r}: unit or description changed",
                )
            )
            bump = _raise_bump(bump, BumpLevel.PATCH)

    for group, label in (
        (zip(old.states, new.states, strict=True), "state"),
        (zip(old.inputs, new.inputs, strict=True), "input"),
        (zip(old.outputs, new.outputs, strict=True), "output"),
    ):
        for o_var, n_var in group:
            if not _variable_cosmetic_equal(o_var, n_var):
                items.append(
                    DiffItem(
                        f"{label}-metadata",
                        f"{label} {o_var.name!r}: unit/description/roles changed",
                    )
                )
                bump = _raise_bump(bump, BumpLevel.PATCH)

    if old.model.description != new.model.description:
        items.append(DiffItem("model-description", "model.description changed"))
        bump = _raise_bump(bump, BumpLevel.PATCH)
    if old.model.source_version != new.model.source_version:
        items.append(
            DiffItem(
                "model-source-version",
                "model.source_version: "
                f"{old.model.source_version!r} -> {new.model.source_version!r}",
            )
        )
        bump = _raise_bump(bump, BumpLevel.PATCH)
    if not _metadata_equal(old.model.metadata, new.model.metadata):
        items.append(DiffItem("model-metadata", "model.metadata changed"))
        bump = _raise_bump(bump, BumpLevel.PATCH)

    if old.profiles != new.profiles:
        items.append(
            DiffItem(
                "profiles",
                f"profiles changed: {old.profiles!r} -> {new.profiles!r}",
            )
        )
        bump = _raise_bump(bump, BumpLevel.PATCH)

    if bump == BumpLevel.NONE:
        items.append(
            DiffItem(
                "unclassified",
                "semantic body differs from baseline but change was not classified; "
                "treat as incompatible (major)",
            )
        )
        return SemanticDiffResult(
            old_hash=old_hash, new_hash=new_hash, bump=BumpLevel.MAJOR, items=items
        )

    return SemanticDiffResult(old_hash=old_hash, new_hash=new_hash, bump=bump, items=items)


def _raise_bump(current: BumpLevel, minimum: BumpLevel) -> BumpLevel:
    order = {BumpLevel.NONE: 0, BumpLevel.PATCH: 1, BumpLevel.MINOR: 2, BumpLevel.MAJOR: 3}
    return current if order[current] >= order[minimum] else minimum


def result_to_jsonable(result: SemanticDiffResult) -> dict[str, Any]:
    """Serialize a diff result for ``--json`` output."""
    return {
        "old_hash": result.old_hash,
        "new_hash": result.new_hash,
        "bump": result.bump.value,
        "items": [{"code": i.code, "message": i.message} for i in result.items],
    }
