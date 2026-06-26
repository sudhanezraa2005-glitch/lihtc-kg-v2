"""Utilities for reading HUD Excel workbooks without mutating Bronze files."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import re
from typing import Iterator
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile


@contextmanager
def iter_repaired_excel_path(path: Path) -> Iterator[Path]:
    """Yield a readable workbook path, repairing invalid core metadata in a temp copy."""
    path = Path(path)
    temp_root = Path(".tmp") / "hud_fmr_excel"
    temp_root.mkdir(parents=True, exist_ok=True)
    repaired_path = temp_root / f"{path.stem}_{uuid4().hex}_repaired{path.suffix}"
    try:
        with ZipFile(path, "r") as source, ZipFile(repaired_path, "w", ZIP_DEFLATED) as target:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == "docProps/core.xml":
                    data = _repair_core_properties(data)
                target.writestr(item, data)
        yield repaired_path
    finally:
        if repaired_path.exists():
            try:
                repaired_path.unlink()
            except PermissionError:
                pass


def _repair_core_properties(data: bytes) -> bytes:
    text = data.decode("utf-8", errors="ignore")
    text = re.sub(
        r"<dcterms:modified[^>]*>.*?</dcterms:modified>",
        '<dcterms:modified xsi:type="dcterms:W3CDTF">2024-01-01T00:00:00Z</dcterms:modified>',
        text,
    )
    text = re.sub(
        r"<dcterms:created[^>]*>.*?</dcterms:created>",
        '<dcterms:created xsi:type="dcterms:W3CDTF">2024-01-01T00:00:00Z</dcterms:created>',
        text,
    )
    return text.encode("utf-8")
