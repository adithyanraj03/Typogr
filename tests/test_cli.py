"""CLI end-to-end: JSON shapes, exit codes, version, determinism."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_cli(*argv):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(
        [PYTHON, "-B", "-m", "typogr", *argv],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_scale_emit_json_shape():
    result = run_cli("scale", "--emit", "json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["base"] == 16 and data["ratio"] == 1.25
    assert data["naming"] == "t-shirt"
    assert [row["step"] for row in data["steps"]] == list(range(-2, 7))
    base = next(row for row in data["steps"] if row["step"] == 0)
    assert set(base) == {"step", "px", "rem", "name"}
    assert base["px"] == 16.0
    assert base["rem"] == 1.0
    assert isinstance(base["name"], str) and base["name"].startswith("--text")


def test_scale_emit_json_matches_global_json_flag():
    a = run_cli("scale", "--emit", "json")
    b = run_cli("scale", "--json")
    assert a.returncode == 0 and b.returncode == 0
    assert json.loads(a.stdout) == json.loads(b.stdout)


def test_scale_config_file_with_flag_override():
    result = run_cli("scale", "--config", "sample\\config.json", "--ratio", "1.2", "--emit", "json")
    if result.returncode != 0:
        result = run_cli("scale", "--config", str(ROOT / "sample" / "config.json"), "--ratio", "1.2", "--emit", "json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["ratio"] == 1.2  # CLI flag overrides the config file


def test_bad_ratio_exits_2():
    result = run_cli("scale", "--ratio", "0")
    assert result.returncode == 2
    assert "ratio" in result.stderr.lower()


def test_pair_json():
    result = run_cli("pair", "--pair", "Georgia,Verdana", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["mode"] == "score"
    assert data["display"] == "Georgia"
    assert data["body"] == "Verdana"
    assert isinstance(data["score"], int)
    assert 0 <= data["score"] <= 100
    assert data["why"].startswith("Rule-based read")
    assert data["warnings"] == []


def test_unknown_font_exits_2():
    result = run_cli("pair", "--pair", "Gorgai,Verdana")
    assert result.returncode == 2
    assert "georgia" in result.stderr


def test_recommend_json_deterministic():
    a = run_cli("pair", "--seed", "1337", "--json")
    b = run_cli("pair", "--seed", "1337", "--json")
    assert a.returncode == 0 and b.returncode == 0
    assert json.loads(a.stdout) == json.loads(b.stdout)
    data = json.loads(a.stdout)
    assert data["mode"] == "recommend"
    assert len(data["pairs"]) == 5


def test_specimen_writes_file(tmp_path):
    out = tmp_path / "specimen.html"
    result = run_cli("specimen", "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "--text-base" in text
    assert "http" not in text.lower()


def test_version():
    result = run_cli("--version")
    assert result.returncode == 0
    assert "1.0.0" in result.stdout
