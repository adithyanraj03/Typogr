"""Scale math: known values, power-not-multiply, guards, naming maps."""

import pytest

from typogr import TypogrError
from typogr import scale

# base 16, ratio 1.25: px = 16 * 1.25 ** step, px 2 dp, rem 4 dp (from raw px)
EXPECTED = {
    -2: (10.24, 0.64),
    -1: (12.8, 0.8),
    0: (16.0, 1.0),
    1: (20.0, 1.25),
    2: (25.0, 1.5625),
    3: (31.25, 1.9531),
    4: (39.06, 2.4414),
    5: (48.83, 3.0518),
    6: (61.04, 3.8147),
}


def test_known_values(known_scale):
    by_step = {row["step"]: row for row in known_scale}
    assert set(by_step) == set(EXPECTED)
    for step, (px, rem) in EXPECTED.items():
        assert by_step[step]["px"] == pytest.approx(px, abs=1e-9)
        assert by_step[step]["rem"] == pytest.approx(rem, abs=1e-9)


def test_known_values_from_brief():
    rows = scale.compute(16, 1.25, 2, 6, 16)
    by_step = {row["step"]: row for row in rows}
    assert by_step[1]["px"] == 20.0
    assert by_step[1]["rem"] == 1.25
    assert by_step[-1]["px"] == 12.8
    assert by_step[3]["px"] == 31.25


def test_power_not_repeated_multiply(known_scale):
    by_step = {row["step"]: row for row in known_scale}
    # 16 * 1.25 ** 4 = 39.0625 -> 39.06 (true power, 2 dp, no drift)
    assert by_step[4]["px"] == 39.06
    assert by_step[4]["rem"] == 2.4414


def test_ratio_zero_or_negative_raises():
    with pytest.raises(TypogrError):
        scale.compute(16, 0, 2, 6, 16)
    with pytest.raises(TypogrError):
        scale.compute(16, -1.2, 2, 6, 16)


def test_base_or_root_zero_raises():
    with pytest.raises(TypogrError):
        scale.compute(0, 1.25, 2, 6, 16)
    with pytest.raises(TypogrError):
        scale.compute(16, 1.25, 2, 6, 0)


def test_ratio_one_warns_constant_scale(capsys):
    rows = scale.compute(16, 1.0, 2, 6, 16)
    err = capsys.readouterr().err
    assert "constant" in err.lower()
    assert len(rows) == 9
    assert all(row["px"] == 16.0 for row in rows)


def test_ratio_below_one_warns_and_descends(capsys):
    rows = scale.compute(16, 0.8, 2, 6, 16)
    err = capsys.readouterr().err
    assert "descend" in err.lower()
    px_values = [row["px"] for row in rows]
    assert px_values == sorted(px_values, reverse=True)


def test_cap_truncates_above_4096(capsys):
    rows = scale.compute(16, 10.0, 0, 6, 16)
    err = capsys.readouterr().err
    assert "4096" in err
    assert [row["step"] for row in rows] == [0, 1, 2]
    assert all(row["px"] <= 4096 for row in rows)


def test_tshirt_names(known_scale):
    names_by_step = {row["step"]: row["name"] for row in known_scale}
    assert names_by_step[0] == "--text-base"
    assert names_by_step[-1] == "--text-sm"
    assert names_by_step[1] == "--text-lg"
    assert names_by_step[2] == "--text-xl"
    assert names_by_step[3] == "--text-2xl"
    assert names_by_step[4] == "--text-3xl"
    assert names_by_step[5] == "--text-4xl"
    assert names_by_step[-2] == "--text-xs"


def test_step_names_include_negative_suffix():
    mapping = scale.names([-2, -1, 0, 2], "step")
    assert mapping[-2] == "--step--2"
    assert mapping[-1] == "--step--1"
    assert mapping[0] == "--step-0"
    assert mapping[2] == "--step-2"


def test_heading_names_top_six_positive():
    rows = scale.compute(16, 1.25, 2, 6, 16, naming="heading")
    names_by_step = {row["step"]: row["name"] for row in rows}
    assert [names_by_step[s] for s in (6, 5, 4, 3, 2, 1)] == [
        "--h1", "--h2", "--h3", "--h4", "--h5", "--h6",
    ]
    # below-base and base steps get no heading token
    assert not any(names_by_step[s].startswith("--h") for s in (-2, -1, 0))


def test_unknown_naming_raises():
    with pytest.raises(TypogrError):
        scale.names([0], "fancy")
