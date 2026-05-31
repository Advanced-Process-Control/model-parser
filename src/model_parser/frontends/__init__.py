"""Frontends: parse authoring formats into the canonical IR."""

from model_parser.frontends.exprtk_ini import (
    ParseResult,
    parse_ini_file,
    parse_ini_text,
)

__all__ = ["ParseResult", "parse_ini_file", "parse_ini_text"]
