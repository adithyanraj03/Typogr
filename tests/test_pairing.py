"""Pairing model: band scores, near-twin cap, recommend, validation."""

import pytest

from typogr import TypogrError
from typogr import pairing


def test_known_pair_score_in_range(full_catalog):
    s = pairing.score("Georgia", "Verdana", full_catalog)
    assert isinstance(s, int)
    assert 0 <= s <= 100
    assert s > 0


def test_known_pair_score_deterministic(full_catalog):
    a = pairing.score("Georgia", "Verdana", full_catalog)
    b = pairing.score("Georgia", "Verdana", full_catalog)
    assert a == b


def test_known_pair_is_case_insensitive(full_catalog):
    assert pairing.score("georgia", "verdana", full_catalog) == pairing.score(
        "Georgia", "Verdana", full_catalog
    )


def test_near_twin_capped_with_flag(full_catalog):
    parts = pairing.score_parts("Georgia", "Times New Roman", full_catalog)
    assert parts["near_twin"] is True
    assert parts["capped"] is True
    assert parts["total"] == 55
    assert parts["total_before_cap"] > 55
    assert "capped at 55" in pairing.why(parts)


def test_near_twin_guard_on_tiny_catalog(tiny_catalog):
    parts = pairing.score_parts("Base Serif", "Twin Serif", tiny_catalog)
    assert parts["near_twin"] is True
    assert parts["total"] <= 55


def test_contrast_sweet_spot_beats_mid(tiny_catalog):
    harmony = pairing.score_parts("Base Serif", "Calm Sans", tiny_catalog)  # diff 0.2
    mid = pairing.score_parts("Base Serif", "Loud Sans", tiny_catalog)      # diff 1.0
    assert harmony["contrast"]["points"] == 30.0
    assert mid["contrast"]["points"] == 0.0
    assert harmony["total"] > mid["total"]


def test_width_band_effect(tiny_catalog):
    in_band = pairing.score_parts("Base Serif", "Calm Sans", tiny_catalog)      # ratio 1.0
    out_band = pairing.score_parts("Base Serif", "Narrow Sans", tiny_catalog)   # ratio 1.375
    assert in_band["width"]["points"] == 30.0
    assert out_band["width"]["points"] < 30.0
    assert in_band["total"] > out_band["total"]


def test_why_is_rule_based_prose(tiny_catalog):
    parts = pairing.score_parts("Base Serif", "Calm Sans", tiny_catalog)
    text = pairing.why(parts)
    assert text.startswith("Rule-based read")
    assert len(text.split(". ")) <= 3  # 1-2 sentences


def test_recommend_deterministic(full_catalog):
    a = pairing.recommend(full_catalog, seed=1337, top=5)
    b = pairing.recommend(full_catalog, seed=1337, top=5)
    assert a == b
    c = pairing.recommend(full_catalog, seed=2024, top=5)
    assert a != c
    assert len(a) == 5
    for item in a:
        assert 0 <= item["score"] <= 100
        assert item["display"] and item["body"]


def test_recommend_order_descending(full_catalog):
    results = pairing.recommend(full_catalog, seed=1337, top=5)
    scores = [item["score"] for item in results]
    assert scores == sorted(scores, reverse=True)


def test_unknown_font_error_suggests_nearest(full_catalog):
    with pytest.raises(TypogrError) as excinfo:
        pairing.score("Gorgai", "Verdana", full_catalog)
    assert "georgia" in str(excinfo.value)


def test_unknown_font_far_from_catalog(full_catalog):
    with pytest.raises(TypogrError) as excinfo:
        pairing.score("Zqxwv", "Verdana", full_catalog)
    assert "available fonts" in str(excinfo.value)


def test_validate_pair_role_warnings(full_catalog):
    assert pairing.validate_pair("Georgia", "Verdana", full_catalog) == []
    warnings = pairing.validate_pair("Verdana", "Georgia", full_catalog)
    assert any("display" in w for w in warnings)
    assert any("body" in w for w in warnings)
