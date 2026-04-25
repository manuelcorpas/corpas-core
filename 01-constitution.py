"""Constitution YAML parser and validator.

Loads 00-constitution.yaml, validates structure, provides typed access.
Caches the parsed result per file path. No side effects at module scope.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml


_cache: dict[str, tuple[str, dict[str, Any]]] = {}


def _default_path() -> Path:
    return Path(__file__).resolve().parents[3] / "00-CORE-MEMORY" / "CONFIGS" / "00-constitution.yaml"


def load(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the constitution YAML. Returns parsed dict.

    Caches by file path; cache is invalidated if file content hash changes.
    """
    p = path or _default_path()
    raw = p.read_text(encoding="utf-8")
    file_hash = hashlib.sha256(raw.encode()).hexdigest()

    key = str(p)
    if key in _cache and _cache[key][0] == file_hash:
        return _cache[key][1]

    data = yaml.safe_load(raw)
    _validate(data)
    _cache[key] = (file_hash, data)
    return data


def file_hash(path: Path | None = None) -> str:
    """Return SHA-256 hex digest of the constitution file."""
    p = path or _default_path()
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _validate(data: dict[str, Any]) -> None:
    """Validate required top-level sections exist."""
    required = [
        "meta", "identity", "decision_rules", "modes",
        "epistemics", "invariants", "decision_ledger",
    ]
    missing = [s for s in required if s not in data]
    if missing:
        raise ValueError(f"Constitution missing required sections: {missing}")

    if data["meta"].get("version") is None:
        raise ValueError("Constitution meta.version is required")

    rules = data["decision_rules"]
    if not isinstance(rules, list) or len(rules) == 0:
        raise ValueError("decision_rules must be a non-empty list")

    for rule in rules:
        if "id" not in rule or "name" not in rule:
            raise ValueError(f"Each decision rule needs 'id' and 'name': {rule}")

    modes = data["modes"]
    if not isinstance(modes, dict):
        raise ValueError("modes must be a mapping")

    invariants = data["invariants"]
    if not isinstance(invariants, list) or len(invariants) == 0:
        raise ValueError("invariants must be a non-empty list")


def get_rules(config: dict[str, Any]) -> list[dict[str, Any]]:
    return config["decision_rules"]


def get_modes(config: dict[str, Any]) -> dict[str, Any]:
    return config["modes"]


def get_invariants(config: dict[str, Any]) -> list[str]:
    return config["invariants"]


def get_epistemics(config: dict[str, Any]) -> dict[str, Any]:
    return config["epistemics"]


def get_identity(config: dict[str, Any]) -> dict[str, Any]:
    return config["identity"]


def get_manipulation_flags(config: dict[str, Any]) -> list[str]:
    md = config.get("manipulation_detection", {})
    return md.get("flags", [])


def get_high_stakes_decisions(config: dict[str, Any]) -> list[str]:
    return config.get("epistemics", {}).get("high_stakes_decisions", [])


def get_forbidden_constructs(config: dict[str, Any]) -> list[str]:
    return config.get("identity", {}).get("voice", {}).get("forbidden_constructs", [])


def get_mission_anchors(config: dict[str, Any]) -> list[str]:
    for rule in config.get("decision_rules", []):
        if rule.get("id") == "R1":
            return rule.get("mission_anchors", [])
    return []
