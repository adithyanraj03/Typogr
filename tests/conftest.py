"""Shared fixtures: project root, catalogs, known scale values."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typogr import scale  # noqa: E402
from typogr import catalog as catalog_mod  # noqa: E402


@pytest.fixture
def project_root():
    return ROOT


@pytest.fixture
def full_catalog():
    """The bundled 14-font sample catalog."""
    return catalog_mod.load(str(ROOT / "sample" / "catalog.json"))


@pytest.fixture
def tiny_catalog():
    """Synthetic fonts with controlled metrics for band tests."""

    def entry(name, category, xh, sc, width):
        return {
            "name": name,
            "category": category,
            "x_height": xh,
            "stroke_contrast": sc,
            "width_ratio": width,
            "stack": name + ", serif",
        }

    fonts = [
        entry("Base Serif", "serif", 0.50, 1.0, 0.55),
        entry("Calm Sans", "sans", 0.50, 0.8, 0.55),
        entry("Loud Sans", "sans", 0.50, 2.0, 0.55),
        entry("Narrow Sans", "sans", 0.50, 1.0, 0.40),
        entry("Twin Serif", "serif", 0.51, 1.0, 0.55),
    ]
    return {font["name"].lower(): font for font in fonts}


@pytest.fixture
def known_scale():
    """base 16, ratio 1.25, two steps below, six above, root 16."""
    return scale.compute(16, 1.25, 2, 6, 16)
