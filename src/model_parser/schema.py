"""JSON Schema export for the canonical IR.

The schema is generated from the Pydantic model so there is a single source of
truth for the IR shape. ``schemas/canonical-ir.schema.json`` is the committed,
versioned artifact that other repositories and languages validate against.
"""

from __future__ import annotations

import json

from model_parser.ir import IR_VERSION, IRModel

SCHEMA_ID = "https://advanced-process-control.github.io/model-parser/canonical-ir.schema.json"


def ir_json_schema() -> dict:
    """Return the JSON Schema for the canonical IR as a dict."""
    schema = IRModel.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = SCHEMA_ID
    schema["title"] = "Canonical Process-Model IR"
    schema["x-ir-version"] = IR_VERSION
    return schema


def dumps_schema() -> str:
    """Return the IR JSON Schema as a pretty JSON string."""
    return json.dumps(ir_json_schema(), indent=2) + "\n"
