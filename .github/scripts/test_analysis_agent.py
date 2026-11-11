#!/usr/bin/env python3
"""Test-analysis agent settings (prompt, tools, schema, limits), shared by CI and local runs.

  ci     print the settings as GitHub step outputs (used by test-analysis.yml)
  local  review a local FlashTest results directory with the local `claude` CLI;
         writes to .test-analysis/, publishes nothing

Example: test_analysis_agent.py local --results DIR [--base REF] [--preview] [--dry-run]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = "claude-opus-5-5"
MAX_TURNS = 60
ALLOWED_TOOLS = ",".join([
    "Read", "Glob", "Grep",
    "Bash(git log:*)", "Bash(git diff:*)", "Bash(git show:*)",
    "Bash(git blame:*)", "Bash(git status:*)",
])
SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["green", "yellow", "red", "incomplete"]},
        "headline": {"type": "string"},
        "report": {"type": "string"},
    },
    "required": ["status", "headline", "report"],
    "additionalProperties": False,
}
MODE_NOTES = {
    "review": "a completed container-run run on GitHub Actions",
    "local": "a local review of FlashTest results from this machine; there are no "
             "GitHub job results, and the working tree may contain uncommitted "
             "changes (see git status and git diff)",
}
# Skip large binaries (HDF5 checkpoints/plots).
MAX_RESULT_FILE = 2 * 1024 * 1024


def render_prompt(mode, sha, branch, base, work):
    text = (HERE / "test_analysis_prompt.md").read_text(encoding="utf-8")
    if text.startswith("<!--"):
        text = text.split("-->", 1)[1].lstrip("\n")
    return Template(text).substitute(MODE=mode, MODE_NOTE=MODE_NOTES[mode], SHA=sha,
                                     BRANCH=branch, BASE=base, WORK=work)


def schema_json():
    return json.dumps(SCHEMA, separators=(",", ":"))


def cmd_ci(args):
    delim = f"EOF_{uuid.uuid4().hex}"
    prompt = render_prompt(args.mode, args.sha, args.branch, args.base, args.work)
    print(f"prompt<<{delim}\n{prompt}\n{delim}")
    print(f"tools={ALLOWED_TOOLS}")
    print(f"schema={schema_json()}")
    print(f"max_turns={MAX_TURNS}")


def git(*a, check=True):
    res = subprocess.run(["git", *a], capture_output=True, text=True)
    if check and res.returncode:
        sys.exit(f"git {' '.join(a)} failed: {res.stderr.strip()}")
    return res.stdout.strip() if res.returncode == 0 else ""


def default_base(head):
    for ref in ("origin/main", "main"):
        mb = git("merge-base", ref, head, check=False)
        if mb and mb != git("rev-parse", head):
            return mb
    return git("rev-parse", f"{head}^", check=False) or git("rev-parse", head)


def copy_results(src, dst):
    copied = skipped = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        if f.stat().st_size > MAX_RESULT_FILE:
            skipped += 1
            continue
        out = dst / f.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        copied += 1
    return copied, skipped


def cmd_local(args):
    root = Path(git("rev-parse", "--show-toplevel"))
    os.chdir(root)
    results = Path(args.results).expanduser().resolve()
    if not results.is_dir():
        sys.exit(f"Not a directory: {results}")
    head = git("rev-parse", args.head)
    base = git("rev-parse", args.base) if args.base else default_base(head)
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "?"
    model = args.model or DEFAULT_MODEL

    work = root / ".test-analysis"
    shutil.rmtree(work, ignore_errors=True)
    (work / "results").mkdir(parents=True)
    (work / ".gitignore").write_text("*\n")
    copied, skipped = copy_results(results, work / "results")
    print(f"Results: {results} ({copied} files copied, {skipped} large files skipped)")

    run = {"url": "local run", "headSha": head, "headBranch": branch,
           "conclusion": "n/a (local)",
           "pipeline": {"mode": "local", "image": "n/a (local results)",
                        "image_build": "not part of this run"},
           "jobs": []}
    (work / "run.json").write_text(json.dumps(run, indent=2))
    subprocess.run([sys.executable, str(HERE / "test_analysis_context.py"),
                    "--results", str(work / "results"), "--base", base, "--head", head,
                    "--run-json", str(work / "run.json"), "--out", str(work / "context.md")],
                   check=True)

    prompt = render_prompt("local", head, branch, base, ".test-analysis")
    (work / "prompt.md").write_text(prompt)
    cmd = ["claude", "-p", prompt, "--model", model, "--max-turns", str(MAX_TURNS),
           "--allowedTools", ALLOWED_TOOLS, "--json-schema", schema_json(),
           "--output-format", "json"]
    print(f"Comparing {base[:8]}..{head[:8]} on {branch}; model {model}")
    print(f"Briefing: {work / 'context.md'}\nPrompt:   {work / 'prompt.md'}")
    if args.dry_run:
        print("Dry run: not calling the model.")
        return

    print("Running Claude Code (this can take several minutes)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    (work / "claude-output.json").write_text(res.stdout)
    try:
        out = json.loads(res.stdout)
    except ValueError:
        sys.exit(f"claude did not return JSON (exit {res.returncode}):\n{res.stderr or res.stdout}")
    review = out.get("structured_output")
    if out.get("is_error") or not isinstance(review, dict):
        sys.exit(f"No report: subtype={out.get('subtype')} result={str(out.get('result'))[:500]}")

    (work / "review.md").write_text(review["report"])
    report = (f"# Pipeline review: {review['status']}\n\n"
              f"Local results `{results}` · tested `{head[:8]}` against `{base[:8]}`\n\n"
              f"**{review['headline']}**\n\n{review['report']}\n")
    (work / "report.md").write_text(report)
    cost = out.get("total_cost_usd")
    print(f"\nStatus: {review['status']}\n{review['headline']}")
    print(f"Turns: {out.get('num_turns')}" + (f", cost: ${cost:.2f}" if cost is not None else ""))
    print(f"Report: {work / 'report.md'}")

    if args.preview:
        meta = {"status": review["status"], "headline": review["headline"],
                "repo_url": "", "run_url": "", "analysis_url": "", "commit": head,
                "base": base, "branch": branch, "model": model,
                "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + " (local)"}
        (work / "meta.json").write_text(json.dumps(meta, indent=2))
        site = work / "site" / "dev"
        site.mkdir(parents=True)
        subprocess.run([sys.executable, str(HERE / "review_page.py"), str(site),
                        str(work / "review.md"), str(work / "meta.json")], check=True)
        print(f"Preview: {site / 'review' / 'index.html'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ci = sub.add_parser("ci", help="print settings as GitHub step outputs")
    for name in ("mode", "sha", "branch", "base", "work"):
        ci.add_argument(f"--{name}", required=True)
    lo = sub.add_parser("local", help="review a local results directory")
    lo.add_argument("--results", required=True, help="FlashTest results (an invocation dir or any parent)")
    lo.add_argument("--base", help="commit to compare against (default: merge-base with main)")
    lo.add_argument("--head", default="HEAD", help="tested commit (default: HEAD)")
    lo.add_argument("--model", help=f"Claude model (default: {DEFAULT_MODEL})")
    lo.add_argument("--preview", action="store_true", help="also render the website page")
    lo.add_argument("--dry-run", action="store_true", help="build briefing and prompt only")
    args = ap.parse_args()
    {"ci": cmd_ci, "local": cmd_local}[args.cmd](args)


if __name__ == "__main__":
    main()
