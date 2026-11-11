#!/usr/bin/env python3
"""Write a Markdown briefing for the test-analysis agent: job outcomes, FlashTest
status per build/run (from the "errors" files) with log tails, and the git changes.

Usage: test_analysis_context.py --results DIR --base SHA --head SHA
                                [--run-json FILE] [--failed-log FILE] [--out FILE]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

INVOCATION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(_\d+)?$")
TAIL = 60
STAGES = ("setup", "compilation", "execution", "testing")


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def tail(path, n=TAIL):
    lines = read_lines(path)
    if not lines:
        return None
    body = "\n".join(lines[-n:])
    skipped = len(lines) - n
    head = f"... ({skipped} earlier lines omitted)\n" if skipped > 0 else ""
    return head + body


def fence(text):
    safe = text.replace("```", "'''")
    return f"```\n{safe}\n```"


def git(*args):
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    return res.stdout.rstrip() if res.returncode == 0 else f"<git {' '.join(args)} failed: {res.stderr.strip()}>"


def build_status(errors_file):
    """Parse a build-level errors file -> (colour, message, failed stage or None)."""
    lines = [ln.strip() for ln in read_lines(errors_file) if ln.strip()]
    changed = bool(lines) and lines[-1] == "!"
    if changed:
        lines = lines[:-1]
    try:
        vals = [int(v) for v in lines]
    except ValueError:
        return "red", "unreadable 'errors' file", None
    if len(vals) < 5:
        return "red", "incomplete 'errors' file (build interrupted?)", None
    setup, comp, exe, test, total = vals[:5]
    same = vals[5] if len(vals) > 5 else 0
    if setup:
        return "red", "failed in setup", "setup"
    if comp:
        return "red", "failed in compilation", "compilation"
    parts, colour, stage = [], "green", None
    if exe:
        colour, stage = "red", "execution"
        parts.append(f"{exe}/{total} runs failed in execution")
    if test:
        if colour != "red":
            colour = "yellow" if test == same else "red"
        stage = stage or "testing"
        parts.append(f"{test}/{total} runs failed in testing" + (" (same as before)" if test == same else ""))
    if not parts:
        parts.append(f"all {total} runs passed")
    if changed:
        parts.append("results changed from previous invocation")
    return colour, "; ".join(parts), stage


def run_status(errors_file):
    lines = [ln.strip() for ln in read_lines(errors_file) if ln.strip()]
    if len(lines) < 2:
        return "?"
    if lines[0] == "1":
        return "failed in execution"
    if lines[1] == "1":
        note = {"!": ", differs from previous", "=": ", same as previous"}.get(lines[2] if len(lines) > 2 else "", "")
        return "failed in testing" + note
    return "passed"


def describe_results(results):
    out = []
    invocations = sorted(p for p in results.rglob("*") if p.is_dir() and INVOCATION_RE.match(p.name))
    if not invocations:
        out.append("**No FlashTest results were found in the downloaded artifacts.** "
                   "The suite probably never ran; check the job conclusions and the failed job logs.")
        return out, {}

    counts = {"green": 0, "yellow": 0, "red": 0}
    for inv in invocations:
        out.append(f"### Invocation `{inv.relative_to(results)}`\n")
        log = inv / "flash_test.log"
        notable = [ln for ln in read_lines(log) if ln.startswith(("ERROR:", "WARNING:"))]
        if notable:
            out.append("flash_test.log errors/warnings:\n" + fence("\n".join(notable[-40:])))
        builds = sorted(p.parent for p in inv.glob("*/errors"))
        if not builds:
            out.append("_No build directories found._\n")
            continue
        out.append("\n| Build | Status | Detail |\n|---|---|---|")
        details = []
        for b in builds:
            colour, msg, stage = build_status(b / "errors")
            counts[colour] += 1
            out.append(f"| `{b.name}` | {colour} | {msg} |")
            if colour == "green":
                continue
            d = [f"#### `{b.name}`: {msg}", f"Directory: `{os.path.relpath(b)}`"]
            files = sorted(f.name for f in b.iterdir() if f.is_file())
            d.append("Files: " + ", ".join(f"`{f}`" for f in files))
            if stage == "setup" and (t := tail(b / "setup_output")):
                d.append("setup_output (tail):\n" + fence(t))
            if stage == "compilation" and (b / "gmake_output").exists():
                errs = [ln for ln in read_lines(b / "gmake_output") if re.search(r"\b(error|Error)\b", ln)]
                if errs:
                    d.append("gmake_output error lines:\n" + fence("\n".join(errs[:40])))
                d.append("gmake_output (tail):\n" + fence(tail(b / "gmake_output") or "<empty>"))
            for r in sorted(p.parent for p in b.glob("*/errors")):
                status = run_status(r / "errors")
                d.append(f"- run `{r.name}`: {status}")
                if status == "passed":
                    continue
                for name in ("test_output", "flash_output"):
                    if t := tail(r / name, 40):
                        d.append(f"  {name} (tail):\n" + fence(t))
            details.append("\n\n".join(d))
        out.append("")
        out.extend(details)
    return out, counts


def describe_changes(base, head):
    out = [f"Range: `{base}..{head}`\n"]
    if base == head:
        out.append("**The tested commit is the same as the base commit: no code changes in range.** "
                   "Differences in outcome point to the environment (image, benchmarks, runner) or flakiness.")
        return out
    out.append("Commits:\n" + fence(git("log", "--no-merges", "--format=%h %an %ad %s", "--date=short", f"{base}..{head}") or "<none>"))
    out.append("Diff stat:\n" + fence(git("diff", "--stat=120", f"{base}..{head}") or "<none>"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--run-json", type=Path)
    ap.add_argument("--failed-log", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    doc = ["# Test analysis briefing\n"]
    if args.run_json and args.run_json.exists():
        run = json.loads(args.run_json.read_text())
        pipe = run.get("pipeline", {})
        doc.append("## Pipeline\n")
        doc.append(f"- Run: {run.get('url')}\n- Mode: {pipe.get('mode', '?')}\n"
                   f"- Branch: `{run.get('headBranch')}`\n- Commit tested: `{run.get('headSha')}`\n"
                   f"- Image: `{pipe.get('image', '?')}`\n"
                   f"- Image build in this run: {pipe.get('image_build') or 'skipped (existing image used)'}\n"
                   f"- Conclusion: **{run.get('conclusion')}**\n")
        if run.get("jobs"):
            doc.append("| Job | Conclusion |\n|---|---|")
            for job in run["jobs"]:
                doc.append(f"| {job.get('name')} | {job.get('conclusion')} |")
            doc.append("")

    results, counts = describe_results(args.results)
    doc.append("## Test results\n")
    if counts:
        doc.append(f"Builds: {counts['green']} green, {counts['yellow']} yellow (known failures), {counts['red']} red\n")
    doc.extend(results)

    if args.failed_log and (t := tail(args.failed_log, 600)):
        doc.append("\n## Failed job logs (last lines of each)\n" + fence(t))

    doc.append("\n## Code changes\n")
    doc.extend(describe_changes(args.base, args.head))

    text = "\n".join(doc) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
