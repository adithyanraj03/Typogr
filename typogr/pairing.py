"""Rule-based display/body pairing scores.

Three geometry bands, weights summing to 100:

  x-height ratio              0.9 - 1.1  -> 40 pts (linear falloff to 0 at 0.6 / 1.5)
  stroke-contrast difference  < 0.3 or > 1.7 -> 30 pts (mid, ~1.0, scores 0)
  width ratio                 0.75 - 1.25 -> 30 pts (linear falloff to 0 at 0.5 / 2.0)

Near-twin guard: same category with x-heights within 0.05 em caps the score
at 55, because two nearly identical faces are a boring pair, not a good one.

All reasoning is rule-based; the prose never fabricates expert attribution.
"""

import random

from typogr import TypogrError
from typogr.catalog import resolve

NEAR_TWIN_CAP = 55
NEAR_TWIN_XH_TOLERANCE = 0.05
_DISPLAY_CATEGORIES = ("serif", "slab")
_BODY_CATEGORIES = ("sans",)


def _band(value, lo, hi, lo_zero, hi_zero, full):
    """Linear band score: full inside [lo, hi], 0 outside [lo_zero, hi_zero]."""
    if lo <= value <= hi:
        return float(full)
    if value < lo:
        if value <= lo_zero:
            return 0.0
        return full * (value - lo_zero) / (lo - lo_zero)
    if value >= hi_zero:
        return 0.0
    return full * (hi_zero - value) / (hi_zero - hi)


def _contrast_points(diff):
    """30 pts at diff <= 0.3 (harmony) or >= 1.7 (clear contrast);
    0 pts at diff == 1.0; linear in between on both sides."""
    if diff <= 0.3:
        return 30.0
    if diff < 1.0:
        return 30.0 * (1.0 - diff) / 0.7
    if diff < 1.7:
        return 30.0 * (diff - 1.0) / 0.7
    return 30.0


def score_parts(display, body, catalog):
    """Full scoring breakdown for a display/body pair (names case-insensitive).

    Returns a dict with the per-band points, the near-twin/cap flags and the
    integer 0-100 ``total`` (cap applied).
    """
    d = resolve(display, catalog)
    b = resolve(body, catalog)
    xh_ratio = float(d["x_height"]) / float(b["x_height"])
    xh_points = _band(xh_ratio, 0.9, 1.1, 0.6, 1.5, 40)
    contrast_diff = abs(float(d["stroke_contrast"]) - float(b["stroke_contrast"]))
    contrast_points = _contrast_points(contrast_diff)
    width_ratio = float(d["width_ratio"]) / float(b["width_ratio"])
    width_points = _band(width_ratio, 0.75, 1.25, 0.5, 2.0, 30)
    near_twin = (
        d["category"] == b["category"]
        and abs(float(d["x_height"]) - float(b["x_height"])) < NEAR_TWIN_XH_TOLERANCE
    )
    total_before_cap = int(round(xh_points + contrast_points + width_points))
    capped = bool(near_twin and total_before_cap > NEAR_TWIN_CAP)
    total = NEAR_TWIN_CAP if capped else total_before_cap
    return {
        "display": d["name"],
        "body": b["name"],
        "x_height": {"ratio": round(xh_ratio, 4), "points": round(xh_points, 1), "max": 40},
        "contrast": {"diff": round(contrast_diff, 4), "points": round(contrast_points, 1), "max": 30},
        "width": {"ratio": round(width_ratio, 4), "points": round(width_points, 1), "max": 30},
        "near_twin": near_twin,
        "capped": capped,
        "total_before_cap": total_before_cap,
        "total": total,
    }


def score(display, body, catalog):
    """The 0-100 integer pairing score (near-twin cap included)."""
    return score_parts(display, body, catalog)["total"]


def why(parts):
    """1-2 plain-English sentences built from the band results.

    Explicitly labelled rule-based; never fabricates expert attribution.
    """
    xh = parts["x_height"]["ratio"]
    cd = parts["contrast"]["diff"]
    wr = parts["width"]["ratio"]
    if 0.9 <= xh <= 1.1:
        xh_clause = (
            "the x-heights sit close (ratio %.2f, inside the 0.9-1.1 band), "
            "so the two faces read as one voice at text size" % xh
        )
    elif xh < 0.9:
        xh_clause = (
            "the display face's x-height is much smaller than the body's "
            "(ratio %.2f), which can make body text look oversized next to headings" % xh
        )
    else:
        xh_clause = (
            "the display face's x-height is much larger than the body's "
            "(ratio %.2f), a strong optical step that risks a mismatched feel" % xh
        )
    if cd <= 0.3:
        contrast_clause = (
            "their stroke contrasts are similar (apart by %.2f), "
            "a harmonious, low-tension choice" % cd
        )
    elif cd >= 1.7:
        contrast_clause = (
            "their stroke contrasts are far apart (apart by %.2f), "
            "a deliberate high-contrast pairing" % cd
        )
    else:
        contrast_clause = (
            "their stroke contrasts sit in the middle (apart by %.2f), "
            "a balanced but unremarkable separation" % cd
        )
    if 0.75 <= wr <= 1.25:
        width_clause = "character widths are well matched (ratio %.2f)" % wr
    else:
        width_clause = (
            "character widths are not well matched (ratio %.2f), "
            "so line lengths will differ noticeably" % wr
        )
    text = "Rule-based read: %s; %s. %s." % (xh_clause, contrast_clause, width_clause)
    if parts.get("capped"):
        text += (
            " The pair is a near-twin (same category, x-heights within 0.05 em), "
            "so the score is capped at %d." % NEAR_TWIN_CAP
        )
    return text


def recommend(catalog, seed=1337, top=5):
    """Top-N display (serif/slab) x sans pairs.

    Candidate pairs are shuffled with random.Random(seed), scored, then
    stably sorted by (-score, display, body). Deterministic per seed.
    """
    displays = [
        entry for entry in catalog.values() if entry.get("category") in _DISPLAY_CATEGORIES
    ]
    bodies = [entry for entry in catalog.values() if entry.get("category") in _BODY_CATEGORIES]
    if not displays or not bodies:
        raise TypogrError("catalog needs at least one serif/slab and one sans font")
    pairs = [(d, b) for d in sorted(displays, key=lambda e: e["name"]) for b in sorted(bodies, key=lambda e: e["name"])]
    rng = random.Random(seed)
    rng.shuffle(pairs)
    scored = []
    for d, b in pairs:
        parts = score_parts(d["name"], b["name"], catalog)
        scored.append(
            {
                "display": d["name"],
                "body": b["name"],
                "score": parts["total"],
                "near_twin": parts["near_twin"],
                "capped": parts["capped"],
            }
        )
    # Stable sort on score alone: equal scores keep their seeded shuffle
    # order, which is what makes the seed matter. Deterministic per seed.
    scored.sort(key=lambda item: -item["score"])
    return scored[:top]


def validate_pair(display, body, catalog):
    """Role check. Returns a list of warning strings (empty = clean).

    Role mismatches are warnings, never errors; unknown fonts do raise.
    """
    d = resolve(display, catalog)
    b = resolve(body, catalog)
    warnings = []
    if d["category"] not in _DISPLAY_CATEGORIES:
        warnings.append(
            "display font %s is %s - display is usually a serif or slab face"
            % (d["name"], d["category"])
        )
    if b["category"] not in _BODY_CATEGORIES:
        warnings.append(
            "body font %s is %s - body is usually a sans face" % (b["name"], b["category"])
        )
    return warnings
