"""Load, save, and hash canonical IR files.

IR files are JSON. Each IR carries a content hash over its semantic body
(everything except the ``provenance`` block, which itself stores the hash) so
that downstream artifacts can reference a scaffold by hash rather than by path
(org contract: "hashes over file paths").
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from model_parser.ir import IRModel


def compute_content_hash(ir: IRModel) -> str:
    """Return the SHA-256 hash of the IR's semantic body (excluding provenance)."""
    body = ir.model_dump(mode="json", exclude={"provenance"})
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_content_hash(ir: IRModel) -> IRModel:
    """Return a copy of ``ir`` with its provenance ``content_hash`` populated."""
    digest = compute_content_hash(ir)
    if ir.provenance is None:
        return ir
    updated = ir.model_copy(deep=True)
    updated.provenance.content_hash = digest
    return updated


def dumps_ir(ir: IRModel) -> str:
    """Serialize an IR to a stable, pretty JSON string."""
    return json.dumps(ir.model_dump(mode="json"), indent=2, sort_keys=False) + "\n"


def save_ir(ir: IRModel, path: str | Path) -> None:
    """Write an IR to ``path`` as JSON."""
    Path(path).write_text(dumps_ir(ir), encoding="utf-8")


def load_ir(path: str | Path) -> IRModel:
    """Load and structurally validate an IR JSON file from ``path``."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return IRModel.model_validate(data)
