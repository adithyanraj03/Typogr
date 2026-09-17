"""Bundled font-metric catalog: load, resolve, suggest.

Font metrics (x-height, stroke contrast, average width) are curated
approximations baked into ``sample/catalog.json``. There is deliberately no
runtime font parsing: fontTools is not stdlib, and typogr must work offline
and deterministically on Python >= 3.9.
"""

import json
from pathlib import Path

from typogr import TypogrError

_BUNDLED_CATALOG = Path(__file__).resolve().parent.parent / "sample" / "catalog.json"
_LEVENSHTEIN_MAX = 3


def levenshtein(a, b):
    """Classic edit distance (insert / delete / substitute)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def load(text_or_path):
    """Load a catalog from a JSON string or a path to a JSON file.

    Accepts either a top-level list of font objects or an object with a
    ``fonts`` key. Returns {lowercase name: entry}.
    """
    path = Path(str(text_or_path))
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = str(text_or_path)
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise TypogrError("catalog is not valid JSON: %s" % exc)
    if isinstance(data, dict) and "fonts" in data:
        data = data["fonts"]
    if not isinstance(data, list):
        raise TypogrError("catalog must be a list of font objects")
    catalog = {}
    for entry in data:
        if not isinstance(entry, dict) or "name" not in entry:
            raise TypogrError("each catalog entry must be an object with a 'name'")
        key = str(entry["name"]).strip().lower()
        if key in catalog:
            raise TypogrError("duplicate font in catalog: %s" % key)
        catalog[key] = dict(entry)
    if not catalog:
        raise TypogrError("catalog is empty")
    return catalog


def default_catalog():
    """The bundled sample catalog."""
    if not _BUNDLED_CATALOG.is_file():
        raise TypogrError("bundled catalog not found at %s" % _BUNDLED_CATALOG)
    return load(_BUNDLED_CATALOG)


def resolve(name, catalog):
    """Case-insensitive font lookup.

    Unknown names raise TypogrError listing the nearest catalog names
    (levenshtein distance <= 3), or the full available list when nothing
    is close.
    """
    key = str(name).strip().lower()
    if key in catalog:
        return catalog[key]
    near = []
    for known in catalog:
        dist = levenshtein(key, known)
        if dist <= _LEVENSHTEIN_MAX:
            near.append((dist, known))
    near.sort()
    if near:
        suggestion = ", ".join(known for _, known in near[:5])
        raise TypogrError("unknown font %r (did you mean: %s?)" % (name, suggestion))
    raise TypogrError(
        "unknown font %r (available fonts: %s)" % (name, ", ".join(sorted(catalog)))
    )
