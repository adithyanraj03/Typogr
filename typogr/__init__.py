"""typogr — offline typography scale & pairing calculator.

Stdlib only (Python >= 3.9), deterministic to the byte.

Subcommands (``python -m typogr``):
  scale     compute a modular type scale (px/rem tokens, CSS export)
  pair      score a display/body pair, or recommend top pairs (seeded)
  specimen  write a self-contained HTML type specimen
"""

__version__ = "1.0.0"


class TypogrError(Exception):
    """User-facing error: invalid input or unknown font.

    The CLI catches this and exits with status 2.
    """
