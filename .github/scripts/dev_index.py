#!/usr/bin/env python3
"""Build dev/index.html for the Flash-MX website.

Usage: dev_index.py <dev-dir>

<dev-dir> holds one directory per branch label, each with a "latest" run and an
optional "passing" run (the last fully passing run, kept only while "latest" is
not passing). Each run is a FlashXTest webview package containing summary.json
and, optionally, run.json written by the workflow: the workflow run URL, commit,
and links to the TestResults-* artifacts that hold the full outputs
(flash_output, HDF5 files, ...) which are not published on the website.
This script only presents what is there; deciding what to keep is done by the
container-run workflow.
"""
import html
import json
import sys
from datetime import datetime, timezone
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
details{margin:.3rem 0} summary{cursor:pointer} ul.artifacts{margin:.2rem 0;padding-left:1.2rem}
td.green{background:var(--green)} td.yellow{background:var(--yellow)} td.red{background:var(--red)}
"""


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def read_run(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def expiry(stamp):
    """Return (expired, YYYY-MM-DD) for an ISO-8601 timestamp, or (False, "")."""
    try:
        when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return False, ""
    return when <= datetime.now(timezone.utc), when.date().isoformat()


def run_links(run):
    """Links to the workflow run and its artifacts (full test outputs)."""
    if not run:
        return []
    esc = html.escape
    out = []
    head = []
    if run.get("commit"):
        sha = esc(run["commit"][:8])
        head.append(f'commit <a href="{esc(run.get("commit_url", ""))}"><code>{sha}</code></a>')
    if run.get("run_url"):
        head.append(f'<a href="{esc(run["run_url"])}">workflow run</a>')
    if head:
        out.append(f'<div class="meta">{" &middot; ".join(head)}</div>')
    items = []
    for a in run.get("artifacts", []):
        expired, date = expiry(a.get("expires_at"))
        name = esc(a.get("name", "artifact"))
        extra = size(a["size_in_bytes"]) if isinstance(a.get("size_in_bytes"), int) else ""
        if expired:
            items.append(f'<li>{name} <span class="meta">(expired {date})</span></li>')
        else:
            if date:
                extra = f"{extra}, available until {date}" if extra else f"available until {date}"
            suffix = f' <span class="meta">({extra})</span>' if extra else ""
            items.append(f'<li><a href="{esc(a.get("url", ""))}">{name}</a>{suffix}</li>')
    if items:
        out += [
            '<details><summary class="meta">Full outputs (flash_output, HDF5 files, logs) '
            "&ndash; GitHub artifacts, sign-in required</summary>",
            f'<ul class="artifacts">{"".join(items)}</ul></details>',
        ]
    return out


def passing(entries):
    return bool(entries) and all(e["colour"] == "green" for e in entries)


def block(label, kind, heading, entries, run):
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
    out += run_links(run)
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
        card += block(label, "latest", "Latest run", latest,
                      read_run(label_dir / "latest" / "run.json"))
        prev = read(label_dir / "passing" / "summary.json")
        if passing(latest):
            card.append('<p class="note">The latest run is also the last successful run.</p>')
        elif prev:
            card += block(label, "passing", "Last successful run", prev,
                          read_run(label_dir / "passing" / "run.json"))
        else:
            card.append('<p class="note">No successful run has been recorded yet.</p>')
        card.append("</div>")
        cards += card

    review_tab = '<a href="review/index.html">Agent review</a>' if (dev_dir / "review" / "index.html").exists() else ""

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dev – Flash-MX</title><style>{CSS}</style></head><body>
<nav><a href="../index.html">Home</a><a href="../about/index.html">About</a><a href="index.html">Dev</a>{review_tab}</nav>
<h1>Development status</h1>
<p>Latest automated test-suite run on each branch, and the last fully successful run when the latest did not pass.</p>
<div class="cards">
{chr(10).join(cards)}
</div></body></html>
"""
    (dev_dir / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
