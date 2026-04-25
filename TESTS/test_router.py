"""Tests for mode router."""


def test_mission_critical_heim(router_mod, config):
    mode = router_mod.classify("Build HEIM validation framework for genomic equity", config)
    assert mode.value == "mission_critical"


def test_mission_critical_clawbio(router_mod, config):
    mode = router_mod.classify("Develop ClawBio architecture for category dominance", config)
    assert mode.value == "mission_critical"


def test_core_responsibility_teaching(router_mod, config):
    mode = router_mod.classify("Mark student essays for Westminster module", config)
    assert mode.value == "core_responsibility"


def test_core_responsibility_supervision(router_mod, config):
    mode = router_mod.classify("Supervision meeting with PhD student", config)
    assert mode.value == "core_responsibility"


def test_decline_off_mission(router_mod, config):
    mode = router_mod.classify("This is completely off-mission and unrelated", config)
    assert mode.value == "decline"


def test_defer_later(router_mod, config):
    mode = router_mod.classify("Defer this until next quarter when funded", config)
    assert mode.value == "defer"


def test_default_fallback(router_mod, config):
    mode = router_mod.classify("Something generic with no keywords", config)
    assert mode.value == "core_responsibility"  # safe default
