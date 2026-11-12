# `.github/` layout

## `workflows/`

GitHub Actions workflows. See `workflows/README.md` for the full list and
trigger conditions.

| File | Purpose |
|---|---|
| `container-run.yml` | Run the Flash-X test suite in the container image, compare against benchmarks, publish results to the website |
| `container-update-image.yml` | Build and publish the test container image to GHCR |
| `container-update-benchmarks.yml` | Regenerate and package benchmark archives |
| `test-analysis.yml` | On-request Claude Code review of a `container-run` run |
| `checks.yml` | Guard: PRs to `main` must come from `staged` |

## Helper code

Helper code invoked by the workflows (and runnable locally).

| Path | Used by | Purpose |
|---|---|---|
| `workflows/pages.py` | `container-run`, `test-analysis` | Build the website's `dev/index.html` and `dev/review/index.html` |
| `agent/agent.py` | `test-analysis` | Drive the Claude Code review agent (CI + local) |
| `agent/agent_context.py` | `agent/agent.py` | Gather git/test context for the review prompt |
| `agent/system.md` | `agent/agent.py` | Review prompt template |
| `agent/tools/` | `agent/agent.py` | Helper scripts invoked by the agent via Bash |

## Local runs

```sh
# Review a local results directory with the local `claude` CLI:
python3 .github/agent/agent.py local --results <dir>

# Rebuild the dev index page:
python3 .github/workflows/pages.py dev <dev-dir>
```

## Notes

- `config`, `execfile`, `test.info` and `__pycache__/` are generated at runtime
  and are gitignored; delete them if they show up untracked.
- Workflow scripts are copied (not symlinked) into `$RUNNER_TEMP` by
  `test-analysis.yml` so the *tested* commit's code is reviewed with *this*
  branch's tooling.
