"""Validation: semantic and profile checks over a canonical IR."""

from model_parser.validation.validators import (
    Diagnostic,
    ValidationReport,
    validate_ir,
)

__all__ = ["Diagnostic", "ValidationReport", "validate_ir"]
