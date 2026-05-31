"""Canonical IR data model.

The IR describes a model **scaffold** only: structure, declarations, and
equations. Concrete numeric parameter values are carried as *defaults* for
bootstrap convenience, but fitted parameter sets and execution scenarios
(initial values, input trajectories, horizons) are deliberately *out of scope*
here — they are sibling contracts (see ADR 0006 and the org contracts page).

The model is a Pydantic v2 model so that the JSON Schema and structural
validation come for free; semantic checks live in :mod:`model_parser.validation`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from model_parser.ir.expr import Expr

IR_VERSION = "0.1.0"
"""SemVer of the IR schema. Major bumps require migration tooling and an ADR."""


class Parameter(BaseModel):
    """A time-independent model parameter declaration."""

    model_config = ConfigDict(extra="forbid")

    name: str
    default: float | None = None
    unit: str | None = None
    description: str | None = None


class Variable(BaseModel):
    """A declared state, input, or output variable.

    ``roles`` carries optional tags such as ``measured``, ``manipulated``,
    ``disturbance``, or ``estimated``.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    unit: str | None = None
    description: str | None = None
    roles: list[str] = Field(default_factory=list)


class Local(BaseModel):
    """A named intermediate expression (an algebraic/observed equation)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    expr: Expr
    unit: str | None = None
    description: str | None = None


class DiffEq(BaseModel):
    """A differential equation ``d(state)/dt = rhs``."""

    model_config = ConfigDict(extra="forbid")

    state: str
    rhs: Expr


class OutputEq(BaseModel):
    """An output equation ``output = rhs``."""

    model_config = ConfigDict(extra="forbid")

    output: str
    rhs: Expr


class Equations(BaseModel):
    """The differential and output equations of the scaffold."""

    model_config = ConfigDict(extra="forbid")

    differential: list[DiffEq] = Field(default_factory=list)
    outputs: list[OutputEq] = Field(default_factory=list)


class ModelInfo(BaseModel):
    """Identity and free-form metadata for the model."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    source_version: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class Provenance(BaseModel):
    """Where this IR came from and which tool produced it."""

    model_config = ConfigDict(extra="forbid")

    tool: str
    created_at: str
    source_format: str | None = None
    source_file: str | None = None
    content_hash: str | None = None


class IRModel(BaseModel):
    """The canonical intermediate representation of a process-model scaffold."""

    model_config = ConfigDict(extra="forbid")

    ir_version: str = IR_VERSION
    model: ModelInfo
    independent_variable: str = "t"
    parameters: list[Parameter] = Field(default_factory=list)
    states: list[Variable] = Field(default_factory=list)
    inputs: list[Variable] = Field(default_factory=list)
    outputs: list[Variable] = Field(default_factory=list)
    locals: list[Local] = Field(default_factory=list)
    equations: Equations = Field(default_factory=Equations)
    profiles: list[str] = Field(default_factory=lambda: ["julia-analysis"])
    provenance: Provenance | None = None

    def symbol_names(self) -> set[str]:
        """Return all declared symbol names (states, inputs, outputs, params, locals)."""
        names: set[str] = set()
        for group in (self.states, self.inputs, self.outputs, self.parameters):
            names |= {item.name for item in group}
        names |= {local.name for local in self.locals}
        return names
