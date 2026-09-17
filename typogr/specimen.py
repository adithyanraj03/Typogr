"""Self-contained HTML type specimen ("Atelier" design).

The document has no external resources of any kind: system font stacks,
inline CSS, and no ``http`` anywhere in the file - it renders identically
offline and prints cleanly.
"""

import html

from typogr import __version__

# Atelier palette, verbatim from DesignTemplate/base.css.
_TOKEN_CSS = """:root {
  --paper: #DFDFDF;
  --surface: #DFDFDB;
  --card: #DFDFDF;
  --ink: #252524;
  --ink-2: #676662;
  --ink-3: #94938C;
  --hairline: #DCDAD1;
  --hairline-strong: #D4D2C8;
  --serif: Georgia, 'Times New Roman', Times, serif;
  --sans: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --leading-body: 1.65;
  --sp-4: 16px;
  --sp-5: 20px;
  --sp-6: 24px;
  --sp-7: 32px;
  --sp-8: 40px;
}
"""

_LAYOUT_CSS = """* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 15px;
  line-height: var(--leading-body);
  padding: 48px 56px;
}
.caps {
  font-family: var(--sans);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin: 0 0 8px;
}
h1.display {
  font-size: 64px;
  font-weight: 700;
  line-height: 1.1;
  margin: 4px 0 0;
}
.hero-body { font-size: 19px; color: var(--ink-2); margin: 10px 0 0; }
.rule { border: 0; border-top: 1px solid var(--hairline-strong); margin: 28px 0; }
.score {
  background: var(--surface);
  border: 1px solid var(--hairline-strong);
  padding: 14px 16px;
  margin: 24px 0;
  max-width: 720px;
}
.score-line { margin: 0 0 6px; font-size: 14px; font-weight: 600; }
.score-line .num { font-family: var(--serif); font-size: 24px; font-weight: 700; }
.score-why { margin: 0; font-size: 13px; color: var(--ink-2); }
.row {
  display: flex;
  align-items: baseline;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--hairline);
}
.row .glyph { font-weight: 700; line-height: 1; white-space: nowrap; }
.row .token {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-3);
  min-width: 132px;
}
.row .meta {
  margin-left: auto;
  font-size: 12px;
  color: var(--ink-3);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
footer { margin-top: 32px; font-size: 11px; color: var(--ink-3); }
"""

_PRINT_CSS = """@media print {
  body { background: #fff; padding: 24px; }
  .score, .row { break-inside: avoid; }
}
"""


def _fmt_ratio(value):
    return "%g" % float(value)


def _fmt_size(value):
    return "%g" % float(value)


def build(scale_rows, display, body, score_info=None, base=16.0, ratio=1.25):
    """Render the complete self-contained specimen document.

    scale_rows : rows from ``scale.compute`` (each ``{step, px, rem, name}``)
    display    : CSS font stack string for the display face
    body       : CSS font stack string for the body face
    score_info : optional ``{display, body, score, why}`` for the banner
    """
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Type specimen - typogr</title>",
        "<style>",
        _TOKEN_CSS,
        ":root {",
        "  --display: %s;" % display,
        "  --body: %s;" % body,
        "}",
        _LAYOUT_CSS,
        _PRINT_CSS,
        "</style>",
        "</head>",
        "<body>",
        "  <header>",
        '    <p class="caps">typogr - offline type specimen</p>',
        '    <h1 class="display" style="font-family: var(--display)">The quick brown fox</h1>',
        '    <p class="hero-body" style="font-family: var(--body)">The quick brown fox</p>',
        "  </header>",
        '  <hr class="rule">',
    ]
    if score_info:
        lines.extend(
            [
                '  <div class="score">',
                '    <p class="score-line">Pairing score <span class="num">%d / 100</span> \u2014 %s \u00d7 %s</p>'
                % (
                    int(score_info["score"]),
                    html.escape(str(score_info["display"]), quote=False),
                    html.escape(str(score_info["body"]), quote=False),
                ),
                '    <p class="score-why">%s</p>'
                % html.escape(str(score_info.get("why", "")), quote=False),
                "  </div>",
            ]
        )
    lines.append("  <section>")
    lines.append(
        '    <p class="caps">scale \u2014 %s ratio \u00b7 base %s px</p>'
        % (_fmt_ratio(ratio), _fmt_size(base))
    )
    for row in scale_rows:
        lines.extend(
            [
                '      <div class="row">',
                '        <span class="token">%s</span>' % html.escape(row["name"], quote=False),
                '        <span class="glyph" style="font-family: var(--display); font-size: %.2fpx">Aa</span>'
                % row["px"],
                '        <span class="meta">Aa \u2014 %.2f px / %.4f rem</span>' % (row["px"], row["rem"]),
                "      </div>",
            ]
        )
    lines.append("  </section>")
    lines.append(
        "  <footer>generated by typogr %s \u2014 rule-based pairing, offline, deterministic to the byte</footer>"
        % __version__
    )
    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines) + "\n"
