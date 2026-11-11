#!/usr/bin/env python3
"""Build the Flash-MX website pages for dev results.

Subcommands:
  dev <dev-dir>                           rebuild dev/index.html
  review <dev-dir> <report.md> <meta.json> write dev/review/index.html
"""
import html
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


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

EXTRA_CSS = """
.badge{display:inline-block;padding:.1rem .6rem;border-radius:4px;font-weight:600;margin-right:.5rem}
.badge.green{background:var(--green)} .badge.yellow,.badge.incomplete{background:var(--yellow)}
.badge.red{background:var(--red)}
.report{margin-top:1rem;overflow-wrap:break-word} .report table{width:max-content;min-width:100%;border-collapse:collapse;margin:.5rem 0} .report th,.report td{overflow-wrap:normal;word-break:keep-all;white-space:nowrap;padding:.3rem .7rem} .report td:first-child,.report th:first-child{white-space:normal}
pre{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:.6rem;overflow-x:auto;white-space:pre-wrap}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}
"""

MARKED = "https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"
PURIFY = "https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data


def size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def expiry(stamp):
    try:
        when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return False, ""
    return when <= datetime.now(timezone.utc), when.date().isoformat()


class DevIndex:
    EMOJI = {"green": "✅", "yellow": "⚠️", "red": "❌"}

    def __init__(self, dev_dir):
        self.dev_dir = Path(dev_dir)

    def run_links(self, run):
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

    def passing(self, entries):
        return bool(entries) and all(e["colour"] == "green" for e in entries)

    def block(self, label, kind, heading, entries, run):
        out = [f"<h3>{html.escape(heading)}</h3>"]
        for e in entries:
            c = e["counts"]
            inv = html.escape(e["invocation"])
            out += [
                f'<div class="meta">{html.escape(e["site"])} &middot; invocation '
                f'<a href="{html.escape(label)}/{kind}/invocations/{inv}.html">{inv}</a></div>',
                "<table><tr><th>Overall</th><th>Passed</th><th>Warnings</th><th>Failed</th><th>Total</th></tr>",
                f'<tr><td class="{e["colour"]}">{self.EMOJI.get(e["colour"], "?")}</td><td>{c["green"]}</td>'
                f'<td>{c["yellow"]}</td><td>{c["red"]}</td><td>{sum(c.values())}</td></tr></table>',
            ]
        out += self.run_links(run)
        out.append(f'<p><a href="{html.escape(label)}/{kind}/index.html">Run details &rarr;</a></p>')
        return out

    def build(self):
        dev_dir = self.dev_dir
        cards = []
        for label_dir in sorted(p for p in dev_dir.iterdir() if p.is_dir()):
            latest = read_json(label_dir / "latest" / "summary.json")
            if not latest:
                continue
            label = label_dir.name
            card = ['<div class="card">', f"<h2>{html.escape(label)}</h2>"]
            card += self.block(label, "latest", "Latest run", latest,
                               read_json(label_dir / "latest" / "run.json") or {})
            prev = read_json(label_dir / "passing" / "summary.json")
            if self.passing(latest):
                card.append('<p class="note">The latest run is also the last successful run.</p>')
            elif prev:
                card += self.block(label, "passing", "Last successful run", prev,
                                   read_json(label_dir / "passing" / "run.json") or {})
            else:
                card.append('<p class="note">No successful run has been recorded yet.</p>')
            card.append("</div>")
            cards += card

        review_tab = '<a href="review/index.html">Review</a>' if (dev_dir / "review" / "index.html").exists() else ""
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


class Review:
    def __init__(self, dev_dir):
        self.dev_dir = Path(dev_dir)

    def link(self, url, text):
        return f'<a href="{html.escape(url)}">{text}</a>' if url else text

    def build(self, report_path, meta_path):
        dev_dir = self.dev_dir
        report = Path(report_path).read_text(encoding="utf-8")
        meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        esc = html.escape
        repo = meta.get("repo_url", "")
        sha, base = meta.get("commit", ""), meta.get("base", "")
        status = meta.get("status", "incomplete")
        if status not in ("green", "yellow", "red", "incomplete"):
            status = "incomplete"

        facts = [f"branch <code>{esc(meta.get('branch', '?'))}</code>"]
        if sha:
            facts.append("tested " + self.link(f"{repo}/commit/{sha}", f"<code>{esc(sha[:8])}</code>"))
        if base and base != sha:
            facts.append("changes " + self.link(f"{repo}/compare/{base}...{sha}",
                                           f"<code>{esc(base[:8])}..{esc(sha[:8])}</code>"))
        facts.append(self.link(meta.get("run_url", ""), "test run"))
        facts.append(self.link(meta.get("analysis_url", ""), "analysis run"))
        when = f"{esc(meta.get('generated', ''))} &middot; {esc(meta.get('model', ''))}"

        data = json.dumps(report).replace("</", "<\\/")

        webview_link = ""
        if (dev_dir / "review" / "webview" / "index.html").exists():
            webview_link = '<p><a href="webview/index.html">Full test results (flashxtest webview) &rarr;</a></p>'

        page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review – Flash-MX</title><style>{CSS}{EXTRA_CSS}</style></head><body>
<nav><a href="../../index.html">Home</a><a href="../../about/index.html">About</a><a href="../index.html">Dev</a><a href="index.html">Review</a></nav>
<h1>Review</h1>
<p>Latest on-request analysis of a test-suite run against the code changes behind it, written by an automated review (Claude).
It can be wrong: treat it as a starting point and verify before acting.</p>
<div class="card">
<h2><span class="badge {status}">{esc(status)}</span>{esc(meta.get("headline", ""))}</h2>
<div class="meta">{" &middot; ".join(facts)}</div>
<div class="meta">{when}</div>
{webview_link}
<div class="report" id="report"><pre>{esc(report)}</pre></div>
</div>
<script type="application/json" id="report-md">{data}</script>
<script src="{MARKED}"></script>
<script src="{PURIFY}"></script>
<script>
try {{
  const md = JSON.parse(document.getElementById("report-md").textContent);
  document.getElementById("report").innerHTML = DOMPurify.sanitize(marked.parse(md));
}} catch (e) {{ /* keep the plain-text fallback */ }}
</script>
</body></html>
"""
        out = dev_dir / "review"
        out.mkdir(parents=True, exist_ok=True)
        for stale in ("index.html", "review.md", "meta.json"):
            (out / stale).unlink(missing_ok=True)
        (out / "index.html").write_text(page, encoding="utf-8")
        (out / "review.md").write_text(report, encoding="utf-8")
        (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "dev":
        DevIndex(Path(argv[1])).build()
    elif cmd == "review":
        Review(Path(argv[1])).build(argv[2], argv[3])
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
