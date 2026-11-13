"""Markdown briefing for the test-analysis agent: job outcomes, FlashTest status
per build/run (from the "errors" files) with log tails, and the git changes."""
import os
import re
import subprocess

INVOCATION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(_\d+)?$")


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def tail(path, n=60):
    lines = read_lines(path)
    if not lines:
        return None
    skipped = f"... ({len(lines) - n} earlier lines omitted)\n" if len(lines) > n else ""
    return skipped + "\n".join(lines[-n:])


def fence(text):
    return "```\n" + text.replace("```", "'''") + "\n```"


def git(*args):
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    return res.stdout.rstrip() if res.returncode == 0 else f"<git {' '.join(args)} failed: {res.stderr.strip()}>"


def build_status(errors_file):
    """Build-level errors file -> (colour, message, failed stage or None)."""
    lines = [ln.strip() for ln in read_lines(errors_file) if ln.strip()]
    changed = bool(lines) and lines[-1] == "!"
    try:
        vals = [int(v) for v in (lines[:-1] if changed else lines)]
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
    parts = parts or [f"all {total} runs passed"]
    if changed:
        parts.append("results changed from previous invocation")
    return colour, "; ".join(parts), stage


def run_status(errors_file):
    lines = [ln.strip() for ln in read_lines(errors_file) if ln.strip()] + ["", "", ""]
    if lines[0] == "1":
        return "failed in execution"
    if lines[1] == "1":
        return "failed in testing" + {"!": ", differs from previous", "=": ", same as previous"}.get(lines[2], "")
    return "passed" if lines[0] == "0" else "?"


def describe_build(b, msg, stage):
    d = [f"#### `{b.name}`: {msg}", f"Directory: `{os.path.relpath(b)}`",
         "Files: " + ", ".join(f"`{f.name}`" for f in sorted(b.iterdir()) if f.is_file())]
    if stage == "setup" and (t := tail(b / "setup_output")):
        d.append("setup_output (tail):\n" + fence(t))
    if stage == "compilation":
        errs = [ln for ln in read_lines(b / "gmake_output") if re.search(r"\b[Ee]rror\b", ln)]
        if errs:
            d.append("gmake_output error lines:\n" + fence("\n".join(errs[:40])))
        d.append("gmake_output (tail):\n" + fence(tail(b / "gmake_output") or "<empty>"))
    for r in sorted(p.parent for p in b.glob("*/errors")):
        status = run_status(r / "errors")
        d.append(f"- run `{r.name}`: {status}")
        if status != "passed":
            d += [f"  {n} (tail):\n" + fence(t) for n in ("test_output", "flash_output") if (t := tail(r / n, 40))]
    return "\n\n".join(d)


def _group_of(build_name):
    n = build_name.lower()
    if n.startswith("unittest"):
        return "Unit tests"
    if n.startswith("comparison"):
        return "Comparison tests"
    if n.startswith("composite"):
        return "Composite tests"
    return "Pipeline and infrastructure"


def describe_results(results, group=None):
    invocations = sorted(p for p in results.rglob("*") if p.is_dir() and INVOCATION_RE.match(p.name))
    if not invocations:
        return ["**No FlashTest results were found.** The suite probably never ran; "
                "check the job conclusions and the failed job logs."]
    out, counts = [], {"green": 0, "yellow": 0, "red": 0}
    for inv in invocations:
        out.append(f"### Invocation `{inv.relative_to(results)}`\n")
        notable = [ln for ln in read_lines(inv / "flash_test.log") if ln.startswith(("ERROR:", "WARNING:"))]
        if notable:
            out.append("flash_test.log errors/warnings:\n" + fence("\n".join(notable[-40:])))
        rows, details = ["\n| Build | Status | Detail |\n|---|---|---|"], []
        for b in sorted(p.parent for p in inv.glob("*/errors")):
            if group and _group_of(b.name) != group:
                continue
            colour, msg, stage = build_status(b / "errors")
            counts[colour] += 1
            rows.append(f"| `{b.name}` | {colour} | {msg} |")
            if colour != "green":
                details.append(describe_build(b, msg, stage))
        if len(rows) == 1:
            continue
        out += rows + [""] + details
    summary = f"Builds: {counts['green']} green, {counts['yellow']} yellow (known failures), {counts['red']} red\n"
    return [summary] + out


def briefing(results, base, head, run, failed_log=None, group=None, repo_url=None):
    doc = ["# Analysis briefing\n", "## Run\n",
           f"- Run: {run.get('url')}\n- Branch: `{run.get('headBranch')}`\n"
           f"- Commit (anchor): `{head}`\n- Conclusion: **{run.get('conclusion')}**\n"
           + (f"- Group scope: **{group}**\n" if group else "")]
    if repo_url:
        doc.append(f"- Repo URL: {repo_url}\n- Code link base: {repo_url}/blob/{head}/ (append `path#Lline`)\n")
    if run.get("jobs"):
        doc += ["| Job | Conclusion |\n|---|---|"] + [f"| {j['name']} | {j['conclusion']} |" for j in run["jobs"]] + [""]
    doc += ["## Test results\n"] + describe_results(results, group=group)
    if failed_log and (t := tail(failed_log, 400)):
        doc.append("\n## Failed job logs (tail)\n" + fence(t))
    doc.append(f"\n## Recent changes (reference only)\n\nRange: `{base}..{head}`\n"
               "Primary subject remains the source on the branch at the commit above; "
               "this range is context, not the subject.\n")
    if base == head:
        doc.append("**No code changes in range** (tested commit = base). Differences in outcome point to "
                   "the environment (image, benchmarks, runner) or flakiness. "
                   "Result change attribution: the commit cannot change the result because there is "
                   "no code change; any difference is environmental or flaky.")
    else:
        doc.append("Base commit is the reference (last passing container-run on the branch, or the "
                   "merge-base with main, or the parent): its test result is the baseline against "
                   "which 'result changed' is judged.")
        log = git("log", "--no-merges", "--format=%h %an %ad %s", "--date=short", f"{base}..{head}")
        files = git("diff", "--name-only", f"{base}..{head}")
        src_files = "\n".join(f for f in files.splitlines() if f.startswith(("source/", "bin/")))
        doc += ["Commits:\n" + fence(log or "<none>"),
                "Changed files:\n" + fence(files or "<none>"),
                "Changed source/bin files (highest priority):\n" + fence(src_files or "<none>"),
                "Diff stat:\n" + fence(git("diff", "--stat=120", f"{base}..{head}") or "<none>")]
    return "\n".join(doc) + "\n"
