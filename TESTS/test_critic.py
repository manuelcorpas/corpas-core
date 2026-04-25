"""Tests for critic output scoring."""


def test_clean_output_passes(critic_mod, config):
    result = critic_mod.critique(
        "The HEIM framework provides a standardised approach to genomic equity assessment.",
        config,
    )
    assert result.passed is True
    assert result.score >= 0.8


def test_hype_language_caught(critic_mod, config):
    result = critic_mod.critique(
        "This is a revolutionary and groundbreaking approach to genomics.",
        config,
    )
    assert any("hype_language" in v for v in result.violations)
    assert result.score < 1.0


def test_empty_pleasantries_caught(critic_mod, config):
    result = critic_mod.critique(
        "I hope this email finds you well. I wanted to discuss the project.",
        config,
    )
    assert any("empty_pleasantries" in v for v in result.violations)


def test_ai_sounding_caught(critic_mod, config):
    result = critic_mod.critique(
        "We should leverage cutting-edge AI to harness the power of genomics and delve into the landscape of precision medicine.",
        config,
    )
    ai_violations = [v for v in result.violations if "ai_sounding" in v]
    assert len(ai_violations) > 0


def test_apologetic_caught(critic_mod, config):
    result = critic_mod.critique(
        "Sorry to bother you, apologies for the delay in responding.",
        config,
    )
    assert any("apologetic" in v for v in result.violations)


def test_em_dash_caught(critic_mod, config):
    result = critic_mod.critique(
        "The framework \u2014 which is novel \u2014 addresses equity.",
        config,
    )
    assert any("em_dash" in v for v in result.violations)


def test_send_requires_approval(critic_mod, config):
    result = critic_mod.critique(
        "Please send this report to the funding body for review.",
        config,
    )
    assert result.requires_principal_approval is True


def test_multiple_violations_lower_score(critic_mod, config):
    result = critic_mod.critique(
        "I hope this finds you well. This is a revolutionary, groundbreaking, "
        "game-changing approach. Sorry for the delay. We should leverage AI "
        "to delve into the landscape of genomics.",
        config,
    )
    assert result.score < 0.5
    assert result.passed is False
