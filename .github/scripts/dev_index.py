#!/usr/bin/env python3
"""Build dev/index.html for the Flash-MX website.

Usage: dev_index.py <dev-dir>

<dev-dir> holds one directory per branch label, each with a "latest" run and an
optional "passing" run (the last fully passing run, kept only while "latest" is
not passing). Each run is a FlashXTest webview package containing summary.json.
This script only presents what is there; deciding what to keep is done by the
container-run workflow.
"""
import html
import json
import sys
from pathlib import Path

EMOJI = {"green": "✅", "yellow": "⚠️", "red": "❌"}

CSS = """
:root{--bg:#f0f4f8;--surface:#fff;--border:#d0d7de;--text:#1f2329;--muted:#57606a;--primary:#1565a0;
--green:#d4edda;--yellow:#fff3cd;--red:#f8d7da}
@media (prefers-color-scheme:dark){:root{--bg:#10151b;--surface:#1a212a;--border:#2f3a46;--text:#e6edf3;
--muted:#9aa7b4;--primary:#6cb2eb;--green:#1e4d2b;--yellow:#5a4a14;--red:#5c2227}}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);
color:var(--text);margin:0;padding:1.5rem 2rem;line-height:1.5}
a{color:var(--primary)} h1{margin:.2rem 0 .5rem} h2{margin:0 0 .25rem} h3{margin:.8rem 0 .2rem;color:var(--muted);font-size:1rem}
nav{display:flex;gap:1.25rem;margin-bottom:1.25rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(22rem,1fr));gap:1rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:1rem 1.25rem}
.meta,.note{color:var(--muted);font-size:.9rem} .note{font-style:italic}
table{border-collapse:collapse;margin:.3rem 0} th,td{border:1px solid var(--border);padding:.3rem .7rem;text-align:left}
td.green{background:var(--green)} td.yellow{background:var(--yellow)} td.red{background:var(--red)}
"""


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def passing(entries):
    return bool(entries) and all(e["colour"] == "green" for e in entries)


def block(label, kind, heading, entries):
    out = [f"<h3>{html.escape(heading)}</h3>"]
    for e in entries:
        c = e["counts"]
        inv = html.escape(e["invocation"])
        out += [
            f'<div class="meta">{html.escape(e["site"])} &middot; invocation '
            f'<a href="{html.escape(label)}/{kind}/invocations/{inv}.html">{inv}</a></div>',
            "<table><tr><th>Overall</th><th>Passed</th><th>Warnings</th><th>Failed</th><th>Total</th></tr>",
            f'<tr><td class="{e["colour"]}">{EMOJI.get(e["colour"], "?")}</td><td>{c["green"]}</td>'
            f'<td>{c["yellow"]}</td><td>{c["red"]}</td><td>{sum(c.values())}</td></tr></table>',
        ]
    out.append(f'<p><a href="{html.escape(label)}/{kind}/index.html">Run details &rarr;</a></p>')
    return out


def main(dev_dir):
    cards = []
    for label_dir in sorted(p for p in dev_dir.iterdir() if p.is_dir()):
        latest = read(label_dir / "latest" / "summary.json")
        if not latest:
            continue
        label = label_dir.name
        card = ['<div class="card">', f"<h2>{html.escape(label)}</h2>"]
        card += block(label, "latest", "Latest run", latest)
        prev = read(label_dir / "passing" / "summary.json")
        if passing(latest):
            card.append('<p class="note">The latest run is also the last successful run.</p>')
        elif prev:
            card += block(label, "passing", "Last successful run", prev)
        else:
            card.append('<p class="note">No successful run has been recorded yet.</p>')
        card.append("</div>")
        cards += card

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dev – Flash-MX</title><style>{CSS}</style></head><body>
<nav><a href="../index.html">Home</a><a href="../about/index.html">About</a><a href="index.html">Dev</a></nav>
<h1>Development status</h1>
<p>Latest automated test-suite run on each branch, and the last fully successful run when the latest did not pass.</p>
<div class="cards">
{chr(10).join(cards)}
</div></body></html>
"""
    (dev_dir / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
