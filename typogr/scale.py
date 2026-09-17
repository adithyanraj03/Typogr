"""Modular type-scale math.

Pure functions, stdlib only. The one rule that matters:

    px = base * ratio ** step

a true power, not a repeated multiply, so long scales do not drift.
px is rounded to 2 decimals; rem = px / root is rounded to 4 decimals
(1.5625rem is legitimate and kept). rem is derived from the unrounded
px so that rounding never compounds.
"""

import sys

from typogr import TypogrError

PX_CAP = 4096.0
NAMINGS = ("t-shirt", "step", "heading")


def _warn(message):
    sys.stderr.write("typogr: warning: %s\n" % message)


def names(steps, naming):
    """Map step numbers to CSS token names for the given naming scheme.

    t-shirt : base at --text-base; --text-sm / --text-xs below,
              --text-lg, --text-xl, --text-2xl, --text-3xl above;
              extra steps extend --text-4xl ... upward and
              --text-2xs ... downward.
    step    : --step-<n> literally, so negative steps become
              --step--1 (valid CSS custom-property names).
    heading : --h1 ... --h6 on the top six positive steps
              (--h1 is the largest).

    Returns a dict {step: token}.
    """
    if naming not in NAMINGS:
        raise TypogrError(
            "unknown naming scheme %r (expected one of: %s)" % (naming, ", ".join(NAMINGS))
        )
    mapping = {}
    if naming == "heading":
        positive = sorted((s for s in steps if s > 0), reverse=True)[:6]
        for index, step in enumerate(positive):
            mapping[step] = "--h%d" % (index + 1)
        return mapping
    for step in steps:
        if naming == "step":
            mapping[step] = "--step-%d" % step
        elif step == 0:
            mapping[step] = "--text-base"
        elif step == 1:
            mapping[step] = "--text-lg"
        elif step == 2:
            mapping[step] = "--text-xl"
        elif step >= 3:
            mapping[step] = "--text-%dxl" % (step - 1)
        elif step == -1:
            mapping[step] = "--text-sm"
        elif step == -2:
            mapping[step] = "--text-xs"
        else:
            mapping[step] = "--text-%dxxs" % (-(step + 1))
    return mapping


def compute(base, ratio, below, above, root, naming="t-shirt"):
    """Compute a scale: a list of {step, px, rem, name} rows, step ascending.

    User errors (TypogrError, CLI exit 2):
      base <= 0, root <= 0, ratio <= 0, negative step counts.
    Warnings (to stderr, not fatal):
      ratio == 1 -> constant scale (every step equals base)
      ratio < 1  -> scale descends as the step grows
      px > 4096  -> steps beyond the cap are truncated
    """
    base = float(base)
    ratio = float(ratio)
    below = int(below)
    above = int(above)
    root = float(root)
    if base <= 0:
        raise TypogrError("base must be > 0 (got %s)" % base)
    if root <= 0:
        raise TypogrError("root must be > 0 (got %s)" % root)
    if ratio <= 0:
        raise TypogrError("ratio must be > 0 (got %s)" % ratio)
    if below < 0 or above < 0:
        raise TypogrError("step counts must be >= 0 (got below=%d above=%d)" % (below, above))
    if ratio == 1:
        _warn("ratio == 1: constant scale, every step equals base (%g px)" % base)
    if ratio < 1:
        _warn("ratio < 1: scale descends as the step grows")

    all_steps = list(range(-below, above + 1))
    # True power, never a repeated multiply.
    raw = [(step, base * (ratio ** step)) for step in all_steps]
    kept = [item for item in raw if item[1] <= PX_CAP]
    dropped = [item for item in raw if item[1] > PX_CAP]
    if dropped:
        _warn(
            "px > %d: truncated %d step(s): %s"
            % (int(PX_CAP), len(dropped), ", ".join("%+d" % s for s, _ in dropped[:8]))
        )
    if not kept:
        raise TypogrError(
            "every step exceeds the %d px cap; lower the ratio or the base" % int(PX_CAP)
        )

    name_map = names([step for step, _ in kept], naming)
    rows = []
    for step, px_raw in kept:
        rows.append(
            {
                "step": step,
                "px": round(px_raw, 2),
                "rem": round(px_raw / root, 4),
                "name": name_map.get(step, "--step-%d" % step),
            }
        )
    return rows
