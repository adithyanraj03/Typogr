"""Specimen document: tokens, Aa rows, stacks, print rules, no http."""

from typogr import specimen


def test_specimen_contains_every_token_and_aa_rows(known_scale):
    html_text = specimen.build(
        known_scale,
        "Georgia, 'Times New Roman', Times, serif",
        "system-ui, 'Segoe UI', Arial, sans-serif",
        None,
    )
    for row in known_scale:
        assert row["name"] in html_text
        assert "%.2f" % row["px"] in html_text
        assert "%.4f" % row["rem"] in html_text
    assert html_text.count("Aa") >= len(known_scale)
    assert "The quick brown fox" in html_text
    assert "@media print" in html_text
    assert "sans-serif" in html_text
    assert "Times, serif" in html_text
    assert "http" not in html_text.lower()


def test_specimen_score_banner(known_scale):
    score_info = {
        "display": "Georgia",
        "body": "Verdana",
        "score": 82,
        "why": "Rule-based read: the x-heights sit close.",
    }
    html_text = specimen.build(
        known_scale, "Georgia, serif", "Arial, sans-serif", score_info
    )
    assert "Pairing score" in html_text
    assert "82 / 100" in html_text
    assert "Georgia \u00d7 Verdana" in html_text
    assert "Rule-based read" in html_text
    assert "http" not in html_text.lower()


def test_specimen_no_banner_when_unscored(known_scale):
    html_text = specimen.build(known_scale, "Georgia, serif", "Arial, sans-serif")
    assert "Pairing score" not in html_text


def test_specimen_deterministic(known_scale):
    a = specimen.build(known_scale, "Georgia, serif", "Arial, sans-serif")
    b = specimen.build(known_scale, "Georgia, serif", "Arial, sans-serif")
    assert a == b
