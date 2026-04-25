"""Decision Ledger: append-only JSONL writer and reader.

Every governance decision is logged here for retrospective audit.
File is created at runtime, never at import time. No side effects at module scope.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from importlib.util import spec_from_file_location, module_from_spec

_models_spec = spec_from_file_location("models", Path(__file__).parent / "00-models.py")
_models = module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models)
LedgerEntry = _models.LedgerEntry


def _default_path() -> Path:
    return Path(__file__).resolve().parents[3] / "00-CORE-MEMORY" / "MEMORY" / "decision_ledger.jsonl"


def append(entry: LedgerEntry, path: Path | None = None) -> None:
    """Append a validated ledger entry as one JSONL line."""
    p = path or _default_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    line = entry.model_dump_json() + "\n"
    with open(p, "a", encoding="utf-8") as f:
        f.write(line)


def read_last(n: int = 10, path: Path | None = None) -> list[LedgerEntry]:
    """Read the last N entries from the ledger."""
    p = path or _default_path()
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    recent = lines[-n:] if len(lines) >= n else lines
    entries = []
    for line in recent:
        if line.strip():
            entries.append(LedgerEntry.model_validate_json(line))
    return entries


def read_all(path: Path | None = None) -> list[LedgerEntry]:
    """Read all entries from the ledger."""
    p = path or _default_path()
    if not p.exists():
        return []
    entries = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        if line.strip():
            entries.append(LedgerEntry.model_validate_json(line))
    return entries


def count(path: Path | None = None) -> int:
    """Count total entries in the ledger."""
    p = path or _default_path()
    if not p.exists():
        return 0
    return sum(1 for line in p.read_text(encoding="utf-8").strip().splitlines() if line.strip())
