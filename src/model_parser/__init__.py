"""model-parser: convert process-model definitions to and from a canonical IR.

The package owns the canonical intermediate representation (IR) for process
models and the transformations around it:

- **frontends** parse an authoring format (e.g. ExprTk INI) into the IR;
- **backends** lower the IR into a target view (e.g. a ModelingToolkit Julia
  script);
- **validation** checks an IR against the schema and backend profiles.

See ``docs/design/model-parser.md`` for the authoritative product specification.
"""

from model_parser.ir import IR_VERSION, IRModel

__all__ = ["IRModel", "IR_VERSION", "__version__"]

__version__ = "0.2.1"
