"""Command line interface: ``typogr scale | pair | specimen``.

Exit codes: 0 for success, 2 for user errors (bad flags, invalid ratio,
unknown font, unreadable files). ``--json`` prints machine-readable output;
human output goes to stdout, warnings and errors to stderr.
"""

import argparse
import json
import sys
import textwrap
from pathlib import Path

import typogr.catalog as catalog
import typogr.emit as emit
import typogr.pairing as pairing
import typogr.scale as scale
import typogr.specimen as specimen
from typogr import TypogrError, __version__

EXIT_OK = 0
EXIT_USER_ERROR = 2

DEFAULTS = {
    "base": 16.0,
    "ratio": 1.25,
    "steps_below": 2,
    "steps_above": 6,
    "root": 16.0,
    "naming": "t-shirt",
}


def _fail(message):
    sys.stderr.write("typogr: error: %s\n" % message)
    return EXIT_USER_ERROR


def _warn(message):
    sys.stderr.write("typogr: warning: %s\n" % message)


def _dump(payload):
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _add_common(parser):
    parser.add_argument(
        "--version", action="version", version="typogr %s" % __version__
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="machine-readable JSON on stdout (overrides --emit for scale)",
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="typogr",
        description="Offline typography scale & pairing calculator "
        "(stdlib only, deterministic to the byte).",
    )
    _add_common(parser)
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_scale = sub.add_parser("scale", help="compute a modular type scale")
    _add_common(p_scale)
    p_scale.add_argument("--base", type=float, default=None,
                         help="base font size in px (default 16, or config 'base')")
    p_scale.add_argument("--ratio", type=float, default=None,
                         help="scale ratio (default 1.25, or config 'ratio')")
    p_scale.add_argument("--steps-below", type=int, default=None,
                         help="steps below base (default 2)")
    p_scale.add_argument("--steps-above", type=int, default=None,
                         help="steps above base (default 6)")
    p_scale.add_argument("--root", type=float, default=None,
                         help="root font size for rem math (default 16)")
    p_scale.add_argument("--name", dest="naming", default=None,
                         choices=["t-shirt", "step", "heading"],
                         help="token naming scheme (default t-shirt)")
    p_scale.add_argument("--config", default=None,
                         help="JSON config file; CLI flags always override")
    p_scale.add_argument("--emit", default=None, choices=["css", "table", "json"],
                         help="output format (default table; --json implies json)")

    p_pair = sub.add_parser("pair", help="score a display/body pair or recommend pairs")
    _add_common(p_pair)
    p_pair.add_argument("--display", default=None, help="display font name (catalog)")
    p_pair.add_argument("--body", default=None, help="body font name (catalog)")
    p_pair.add_argument("--pair", default=None,
                        help="'DISPLAY,BODY' - score a specific pair in one flag")
    p_pair.add_argument("--top", type=int, default=5,
                        help="pairs to recommend (default 5)")
    p_pair.add_argument("--seed", type=int, default=1337,
                        help="seed for the recommend order (default 1337)")
    p_pair.add_argument("--catalog", default=None,
                        help="path to an alternate catalog JSON")

    p_spec = sub.add_parser("specimen", help="write a self-contained HTML type specimen")
    _add_common(p_spec)
    p_spec.add_argument("--base", type=float, default=16.0,
                        help="base font size in px (default 16)")
    p_spec.add_argument("--ratio", type=float, default=1.25,
                        help="scale ratio (default 1.25)")
    p_spec.add_argument("--display", default="Georgia",
                        help="display font name from the catalog (default Georgia)")
    p_spec.add_argument("--body", default="system-ui, Arial, sans-serif",
                        help="body font CSS stack (default 'system-ui, Arial, sans-serif')")
    p_spec.add_argument("--out", default="specimen.html",
                        help="output file (default specimen.html)")
    return parser


def _load_config(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise TypogrError("cannot read config %s: %s" % (path, exc))
    except ValueError as exc:
        raise TypogrError("config %s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict):
        raise TypogrError("config must be a JSON object")
    return data


def _pick(flag, config, key):
    """CLI flag wins, then the config file, then the built-in default."""
    if flag is not None:
        return flag
    if key in config:
        return config[key]
    return DEFAULTS[key]


def cmd_scale(args):
    try:
        config = _load_config(args.config) if args.config else {}
        base = float(_pick(args.base, config, "base"))
        ratio = float(_pick(args.ratio, config, "ratio"))
        below = int(_pick(args.steps_below, config, "steps_below"))
        above = int(_pick(args.steps_above, config, "steps_above"))
        root = float(_pick(args.root, config, "root"))
        naming = str(_pick(args.naming, config, "naming"))
        rows = scale.compute(base, ratio, below, above, root, naming=naming)
    except TypogrError as exc:
        return _fail(str(exc))
    if args.json or (args.emit or "table") == "json":
        _dump({"base": base, "ratio": ratio, "root": root, "naming": naming, "steps": rows})
        return EXIT_OK
    fmt = args.emit or "table"
    if fmt == "css":
        sys.stdout.write(emit.css(rows, naming))
    else:
        sys.stdout.write(emit.table(rows))
    return EXIT_OK


def cmd_pair(args):
    try:
        cat = catalog.load(args.catalog) if args.catalog else catalog.default_catalog()
    except TypogrError as exc:
        return _fail(str(exc))
    display = args.display
    body = args.body
    if args.pair is not None:
        left, sep, right = args.pair.partition(",")
        if not sep or not left.strip() or not right.strip():
            return _fail("--pair expects DISPLAY,BODY (for example 'Georgia,Verdana')")
        display, body = left.strip(), right.strip()
    if display is not None or body is not None:
        if display is None or body is None:
            return _fail("pair mode needs both --display and --body, or --pair A,B")
        try:
            parts = pairing.score_parts(display, body, cat)
            warnings = pairing.validate_pair(display, body, cat)
        except TypogrError as exc:
            return _fail(str(exc))
        if args.json:
            _dump({
                "mode": "score",
                "display": parts["display"],
                "body": parts["body"],
                "score": parts["total"],
                "parts": parts,
                "why": pairing.why(parts),
                "warnings": warnings,
            })
            return EXIT_OK
        print("%s \u00d7 %s \u2014 %d / 100" % (parts["display"], parts["body"], parts["total"]))
        print("  x-height  ratio %5.2f   (band 0.90-1.10)      %5.1f / %d"
              % (parts["x_height"]["ratio"], parts["x_height"]["points"], parts["x_height"]["max"]))
        print("  contrast  diff  %5.2f   (sweet <0.30 / >1.70)  %5.1f / %d"
              % (parts["contrast"]["diff"], parts["contrast"]["points"], parts["contrast"]["max"]))
        print("  width     ratio %5.2f   (band 0.75-1.25)       %5.1f / %d"
              % (parts["width"]["ratio"], parts["width"]["points"], parts["width"]["max"]))
        if parts["capped"]:
            print("  near-twin cap: %d -> %d" % (parts["total_before_cap"], parts["total"]))
        for i, line in enumerate(textwrap.fill(pairing.why(parts), width=88).splitlines()):
            print(("  why     %s" if i == 0 else "          %s") % line)
        for warning in warnings:
            print("  warn    %s" % warning)
        return EXIT_OK
    try:
        results = pairing.recommend(cat, args.seed, args.top)
    except TypogrError as exc:
        return _fail(str(exc))
    if args.json:
        _dump({
            "mode": "recommend",
            "seed": args.seed,
            "top": args.top,
            "pairs": [
                {"display": r["display"], "body": r["body"], "score": r["score"]}
                for r in results
            ],
        })
        return EXIT_OK
    print("top %d display x sans pairs (seed %d, rule-based)" % (len(results), args.seed))
    for rank, result in enumerate(results, start=1):
        line = "  %d. %s \u00d7 %s \u2014 %d / 100" % (
            rank, result["display"], result["body"], result["score"]
        )
        if result["capped"]:
            line += " (near-twin cap)"
        print(line)
    return EXIT_OK


def _try_resolve(cat, name):
    try:
        return catalog.resolve(name, cat)
    except TypogrError:
        return None


def cmd_specimen(args):
    try:
        rows = scale.compute(args.base, args.ratio, 2, 6, 16, naming="t-shirt")
    except TypogrError as exc:
        return _fail(str(exc))
    try:
        cat = catalog.default_catalog()
    except TypogrError as exc:
        return _fail(str(exc))
    display_entry = _try_resolve(cat, args.display)
    body_entry = _try_resolve(cat, args.body)
    if display_entry is not None:
        display_stack = display_entry.get("stack") or args.display
    else:
        display_stack = args.display
        _warn("display %r not in catalog; using it as a raw stack and skipping the pairing score"
              % args.display)
    body_stack = (body_entry.get("stack") or args.body) if body_entry is not None else args.body
    score_info = None
    if display_entry is not None and body_entry is not None:
        parts = pairing.score_parts(args.display, args.body, cat)
        score_info = {
            "display": display_entry["name"],
            "body": body_entry["name"],
            "score": parts["total"],
            "why": pairing.why(parts),
        }
    document = specimen.build(rows, display_stack, body_stack, score_info,
                              base=args.base, ratio=args.ratio)
    encoded = document.encode("utf-8")
    out = Path(args.out)
    try:
        if out.parent != Path("."):
            out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(encoded)
    except OSError as exc:
        return _fail("cannot write %s: %s" % (args.out, exc))
    if args.json:
        _dump({
            "out": str(out),
            "bytes": len(encoded),
            "rows": len(rows),
            "score": score_info["score"] if score_info else None,
        })
    else:
        score_text = ", score %d/100" % score_info["score"] if score_info else ""
        print("wrote %s (%d bytes, %d scale steps%s)"
              % (args.out, len(encoded), len(rows), score_text))
    return EXIT_OK


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_OK
    if args.command == "scale":
        return cmd_scale(args)
    if args.command == "pair":
        return cmd_pair(args)
    return cmd_specimen(args)
