#!/usr/bin/env python3
"""Write dev/review/index.html (latest agent review only) from review.md and meta.json.

Usage: review_page.py <dev-dir> <review.md> <meta.json>
"""
import html
import json
import shutil
import sys
from pathlib import Path

from dev_index import CSS

EXTRA_CSS = """
.badge{display:inline-block;padding:.1rem .6rem;border-radius:4px;font-weight:600;margin-right:.5rem}
.badge.green{background:var(--green)} .badge.yellow,.badge.incomplete{background:var(--yellow)}
.badge.red{background:var(--red)}
.report{margin-top:1rem;overflow-wrap:anywhere} .report table{display:block;overflow-x:auto}
pre{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:.6rem;overflow-x:auto;white-space:pre-wrap}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}
"""

MARKED = "https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"
PURIFY = "https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"


def link(url, text):
    return f'<a href="{html.escape(url)}">{text}</a>' if url else text


def main(dev_dir, report_path, meta_path):
    report = report_path.read_text(encoding="utf-8")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    esc = html.escape
    repo = meta.get("repo_url", "")
    sha, base = meta.get("commit", ""), meta.get("base", "")
    status = meta.get("status", "incomplete")
    if status not in ("green", "yellow", "red", "incomplete"):
        status = "incomplete"

    facts = [f"branch <code>{esc(meta.get('branch', '?'))}</code>"]
    if sha:
        facts.append("tested " + link(f"{repo}/commit/{sha}", f"<code>{esc(sha[:8])}</code>"))
    if base and base != sha:
        facts.append("changes " + link(f"{repo}/compare/{base}...{sha}",
                                       f"<code>{esc(base[:8])}..{esc(sha[:8])}</code>"))
    facts.append(link(meta.get("run_url", ""), "test run"))
    facts.append(link(meta.get("analysis_url", ""), "analysis run"))
    when = f"{esc(meta.get('generated', ''))} &middot; {esc(meta.get('model', ''))}"

    # Escape "</" so the report cannot close the <script> tag.
    data = json.dumps(report).replace("</", "<\\/")

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent review – Flash-MX</title><style>{CSS}{EXTRA_CSS}</style></head><body>
<nav><a href="../../index.html">Home</a><a href="../../about/index.html">About</a><a href="../index.html">Dev</a><a href="index.html">Agent review</a></nav>
<h1>Agent review</h1>
<p>Latest on-request analysis of a test-suite run against the code changes behind it, written by an AI agent (Claude).
It can be wrong: treat it as a starting point and verify before acting.</p>
<div class="card">
<h2><span class="badge {status}">{esc(status)}</span>{esc(meta.get("headline", ""))}</h2>
<div class="meta">{" &middot; ".join(facts)}</div>
<div class="meta">{when}</div>
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
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "review.md").write_text(report, encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
