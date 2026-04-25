"""Tests for constitution YAML parser."""

import pytest
import tempfile
from pathlib import Path


def test_load_valid(constitution_mod, constitution_path):
    config = constitution_mod.load(constitution_path)
    assert config["meta"]["version"] == "0.2.0"
    assert config["meta"]["principal"] == "Manuel Corpas"


def test_load_cached(constitution_mod, constitution_path):
    config1 = constitution_mod.load(constitution_path)
    config2 = constitution_mod.load(constitution_path)
    assert config1 is config2  # same object from cache


def test_file_hash_stable(constitution_mod, constitution_path):
    h1 = constitution_mod.file_hash(constitution_path)
    h2 = constitution_mod.file_hash(constitution_path)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_load_invalid_missing_sections(constitution_mod, tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("meta:\n  version: '1.0'\n")
    with pytest.raises(ValueError, match="missing required sections"):
        constitution_mod.load(bad_yaml)


def test_load_invalid_no_rules(constitution_mod, tmp_path):
    bad_yaml = tmp_path / "bad2.yaml"
    bad_yaml.write_text(
        "meta:\n  version: '1.0'\n"
        "identity: {}\ndecision_rules: []\nmodes: {}\n"
        "epistemics: {}\ninvariants: [x]\ndecision_ledger: {}\n"
    )
    with pytest.raises(ValueError, match="non-empty list"):
        constitution_mod.load(bad_yaml)


def test_get_invariants(constitution_mod, config):
    inv = constitution_mod.get_invariants(config)
    assert len(inv) >= 7
    assert "no_send_authority_without_principal_approval" in inv


def test_get_mission_anchors(constitution_mod, config):
    anchors = constitution_mod.get_mission_anchors(config)
    assert "genomic_equity" in anchors
    assert "HEIM_as_global_standard" in anchors


def test_get_forbidden_constructs(constitution_mod, config):
    fc = constitution_mod.get_forbidden_constructs(config)
    assert "hype_language" in fc
    assert "empty_pleasantries" in fc
