#!/usr/bin/env python3
"""Test-analysis agent: prompt, tools, schema and limits shared by CI and local runs.

  review  CI (test-analysis.yml): reads RUN_ID, SHA, BRANCH, BASE from the environment
          and the run's files in .test-analysis/; writes report.md, review.md, meta.json
  local   review a local FlashTest results directory with the local `claude` CLI

Example: analyze.py local --results DIR [--base REF] [--preview] [--dry-run]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Template

from analysis_context import briefing

HERE = Path(__file__).resolve().parent
WORK = Path(".test-analysis")
DEFAULT_MODEL = "claude-opus-5-5"
MAX_TURNS = 60
ALLOWED_TOOLS = ",".join(["Read", "Glob", "Grep"] + [f"Bash(git {c}:*)" for c in ("log", "diff", "show", "blame", "status")])
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
CONTEXT = {
    "review": "a completed container-run run on GitHub Actions",
    "local": "a local review of FlashTest results from this machine; there are no GitHub job "
             "results, and the working tree may contain uncommitted changes (see git status/diff)",
}
GITHUB_SECRETS = ("GH_TOKEN", "GITHUB_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_URL")
MAX_RESULT_FILE = 2 * 1024 * 1024  # local runs: skip large binaries (HDF5)


def render_prompt(mode, sha, branch, base, prompt=None, prompt_file=None):
    if prompt_file:
        raw = Path(prompt_file).read_text(encoding="utf-8")
    elif prompt:
        raw = prompt
    elif os.environ.get("PROMPT_FILE"):
        raw = Path(os.environ["PROMPT_FILE"]).read_text(encoding="utf-8")
    elif os.environ.get("PROMPT"):
        raw = os.environ["PROMPT"]
    else:
        raw = (HERE / "analysis_prompt.md").read_text(encoding="utf-8")
    text = raw.split("-->", 1)[-1].lstrip() if "-->" in raw else raw
    return Template(text).safe_substitute(CONTEXT=CONTEXT[mode], SHA=sha, BRANCH=branch, BASE=base, WORK=WORK)


def summary(text):
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(text + "\n")


def fail(msg):
    summary(f"**Test analysis failed:** {msg}")
    sys.exit(msg)


def run_claude(prompt, model, env=None):
    cmd = ["claude", "-p", prompt, "--model", model, "--max-turns", str(MAX_TURNS),
           "--allowedTools", ALLOWED_TOOLS, "--json-schema", json.dumps(SCHEMA, separators=(",", ":")),
           "--output-format", "json"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    (WORK / "claude-output.json").write_text(res.stdout)
    try:
        out = json.loads(res.stdout)
    except ValueError:
        fail(f"claude did not return JSON (exit {res.returncode}): {res.stderr or res.stdout}")
    review = out.get("structured_output")
    if out.get("is_error") or not isinstance(review, dict):
        fail(f"no report: {str(out.get('result'))[:500]}")
    cost = out.get("total_cost_usd")
    print(f"{review['status']}: {review['headline']}\nTurns: {out.get('num_turns')}"
          + (f", cost: ${cost:.2f}" if cost is not None else ""))
    return review


def write_outputs(review, meta, source):
    meta = {**meta, "status": review["status"], "headline": review["headline"],
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    report = (f"# Test run review: {review['status']}\n\n{source} · tested `{meta['commit'][:8]}` "
              f"against `{meta['base'][:8]}`\n\n**{review['headline']}**\n\n{review['report']}\n")
    (WORK / "review.md").write_text(review["report"])
    (WORK / "meta.json").write_text(json.dumps(meta, indent=2))
    (WORK / "report.md").write_text(report)
    summary(report)


# --- Credentials (CI) -----------------------------------------------------------

def agent_env(auth):
    """Environment for Claude Code with only the chosen credentials; returns (env, cleanup)."""
    env = {k: v for k, v in os.environ.items() if k not in GITHUB_SECRETS and v != ""}
    if "ANTHROPIC_API_KEY" not in env:
        fail("no Anthropic credentials: set the ANTHROPIC_API_KEY secret")
    print("Anthropic auth: ANTHROPIC_API_KEY secret")
    return env, lambda: None


# --- Commands --------------------------------------------------------------------

def cmd_review(args):
    e = os.environ
    (WORK / "results").mkdir(parents=True, exist_ok=True)
    run = json.loads((WORK / "run.json").read_text())
    (WORK / "context.md").write_text(briefing(WORK / "results", e["BASE"], e["SHA"], run, WORK / "failed-jobs.log"))
    env, cleanup = agent_env(args.auth)
    try:
        print(f"Running Claude Code ({args.model}, up to {MAX_TURNS} turns)...", flush=True)
        review = run_claude(render_prompt("review", e["SHA"], e["BRANCH"], e["BASE"],
                                          prompt=getattr(args, "prompt", None),
                                          prompt_file=getattr(args, "prompt_file", None)), args.model, env)
    finally:
        cleanup()
    repo = f"{e['GITHUB_SERVER_URL']}/{e['GITHUB_REPOSITORY']}"
    meta = {"repo_url": repo, "run_url": f"{repo}/actions/runs/{e['RUN_ID']}",
            "analysis_url": f"{repo}/actions/runs/{e['GITHUB_RUN_ID']}",
            "commit": e["SHA"], "base": e["BASE"], "branch": e["BRANCH"], "model": args.model}
    write_outputs(review, meta, f"Run analyzed: {meta['run_url']}")


def git(*a):
    res = subprocess.run(["git", *a], capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else ""


def cmd_local(args):
    os.chdir(git("rev-parse", "--show-toplevel") or ".")
    results = Path(args.results).expanduser().resolve()
    if not results.is_dir():
        sys.exit(f"Not a directory: {results}")
    head = git("rev-parse", args.head)
    base = git("rev-parse", args.base) if args.base else git("merge-base", "origin/main", head)
    if not base or base == head:
        base = git("rev-parse", f"{head}^") or head
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "?"

    shutil.rmtree(WORK, ignore_errors=True)
    (WORK / "results").mkdir(parents=True)
    (WORK / ".gitignore").write_text("*\n")
    files = [f for f in results.rglob("*") if f.is_file() and f.stat().st_size <= MAX_RESULT_FILE]
    for f in files:
        (WORK / "results" / f.relative_to(results)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, WORK / "results" / f.relative_to(results))
    run = {"url": "local run", "headBranch": branch, "conclusion": "n/a (local)"}
    (WORK / "context.md").write_text(briefing(WORK / "results", base, head, run))
    prompt = render_prompt("local", head, branch, base,
                           prompt=getattr(args, "prompt", None),
                           prompt_file=getattr(args, "prompt_file", None))
    (WORK / "prompt.md").write_text(prompt)
    print(f"{len(files)} result files from {results}; comparing {base[:8]}..{head[:8]} on {branch}")
    print(f"Briefing: {WORK / 'context.md'}, prompt: {WORK / 'prompt.md'}")
    if args.dry_run:
        return

    print("Running Claude Code (this can take several minutes)...")
    review = run_claude(prompt, args.model)
    meta = {"repo_url": "", "run_url": "", "analysis_url": "", "commit": head, "base": base,
            "branch": branch, "model": args.model}
    write_outputs(review, meta, f"Local results `{results}`")
    print(f"Report: {WORK / 'report.md'}")
    if args.preview:
        site = WORK / "site" / "dev"
        site.mkdir(parents=True)
        subprocess.run([sys.executable, str(HERE / "pages.py"), "review", str(site),
                        str(WORK / "review.md"), str(WORK / "meta.json")], check=True)
        print(f"Preview: {site / 'review' / 'index.html'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rv = sub.add_parser("review", help="run the agent in CI")
    rv.add_argument("--auth", choices=("api_key",), default="api_key")
    rv.add_argument("--model", default=DEFAULT_MODEL)
    rv.add_argument("--prompt", help="override the agent prompt text")
    rv.add_argument("--prompt-file", help="read the agent prompt from a file")
    lo = sub.add_parser("local", help="review a local results directory")
    lo.add_argument("--results", required=True, help="FlashTest results directory")
    lo.add_argument("--base", help="commit to compare against (default: merge-base with origin/main)")
    lo.add_argument("--head", default="HEAD")
    lo.add_argument("--model", default=DEFAULT_MODEL)
    lo.add_argument("--preview", action="store_true", help="also render the website page")
    lo.add_argument("--dry-run", action="store_true", help="write briefing and prompt only")
    lo.add_argument("--prompt", help="override the agent prompt text")
    lo.add_argument("--prompt-file", help="read the agent prompt from a file")
    args = ap.parse_args()
    (cmd_review if args.cmd == "review" else cmd_local)(args)


if __name__ == "__main__":
    main()
