"""Tests for strategy aligner (R1-R5 scoring)."""


def test_r1_pass_mission_aligned(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Build HEIM genomic equity framework", config)
    assert rules["R1"].passed is True


def test_r1_fail_off_mission(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Organise office birthday party", config)
    assert rules["R1"].passed is False


def test_r2_fail_overload(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Drop everything and handle this urgent new request ASAP", config)
    assert rules["R2"].passed is False


def test_r2_pass_normal(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Review draft paper on precision medicine", config)
    assert rules["R2"].passed is True


def test_r3_fail_heavy_analysis(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Write a detailed comprehensive report analysing whether we should proceed", config)
    assert rules["R3"].passed is False


def test_r3_pass_prototype(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Build a quick test prototype to check feasibility", config)
    assert rules["R3"].passed is True


def test_r4_fail_one_shot(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("One-off panel appearance with no output", config)
    assert rules["R4"].passed is False


def test_r4_pass_framework(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Build reusable benchmark framework", config)
    assert rules["R4"].passed is True


def test_r5_fail_fragility(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Concentrate all funding on a single funder with vendor lock-in", config)
    assert rules["R5"].passed is False


def test_r5_pass_diversified(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Diversify funding across multiple institutions", config)
    assert rules["R5"].passed is True


def test_verdict_yes_all_pass(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Build HEIM genomic equity benchmark framework", config)
    verdict = aligner_mod.compute_verdict(rules)
    assert verdict.value == "yes"


def test_verdict_no_r1_fail(aligner_mod, config):
    rules = aligner_mod.evaluate_rules("Organise office birthday party", config)
    verdict = aligner_mod.compute_verdict(rules)
    assert verdict.value == "no"
