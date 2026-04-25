"""Shared fixtures for constitution governance tests."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# Add PYTHON/ to sys.path so we can import sibling modules
PYTHON_DIR = Path(__file__).resolve().parent.parent / "PYTHON"
sys.path.insert(0, str(PYTHON_DIR))

from importlib.util import spec_from_file_location, module_from_spec


def _load(name: str, filename: str):
    spec = spec_from_file_location(name, PYTHON_DIR / filename)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def constitution_path():
    return Path(__file__).resolve().parents[3] / "00-CORE-MEMORY" / "CONFIGS" / "00-constitution.yaml"


@pytest.fixture
def config(constitution_path):
    constitution = _load("constitution", "01-constitution.py")
    return constitution.load(constitution_path)


@pytest.fixture
def tmp_ledger(tmp_path):
    return tmp_path / "test_ledger.jsonl"


@pytest.fixture
def models():
    return _load("models", "00-models.py")


@pytest.fixture
def constitution_mod():
    return _load("constitution", "01-constitution.py")


@pytest.fixture
def invariants_mod():
    return _load("invariants", "02-invariants.py")


@pytest.fixture
def router_mod():
    return _load("router", "03-router.py")


@pytest.fixture
def aligner_mod():
    return _load("aligner", "04-strategy_aligner.py")


@pytest.fixture
def critic_mod():
    return _load("critic", "05-critic.py")


@pytest.fixture
def ledger_mod():
    return _load("ledger", "06-decision_ledger.py")


@pytest.fixture
def govern_mod():
    return _load("govern", "07-govern.py")
