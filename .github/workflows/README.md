## GitHub workflows

These workflows run the Flash-X test suite with [`flashxtest`](https://github.com/Flash-X/Flash-X-Test)
inside a Docker container that has AMReX and HYPRE preinstalled, using the
`sites/container` configuration. See `sites/container/README.md` for details.

- **`image.yml`** — build and publish the test image to GHCR (on push to
  `main`/`staged` that changes `sites/container/Dockerfile`, or manual dispatch).
- **`ci.yml`** — run the suite on push to `main` only (after waiting for any
  in-progress image build), compare against benchmarks,
  and publish results to https://flash-mx.github.io/dev, with links back to the run's
  `TestResults-*` artifacts (`flash_output`, HDF5 files, ...). For `staged`, trigger manually
  via `workflow_dispatch` on a tagged commit; results are published only when the commit is
  tagged (or on `main`).
- **`benchmarks.yml`** — regenerate and package benchmarks (manual dispatch).
- **`agent.yml`** — on request (manual dispatch): a Claude Code agent reviews the latest
  `ci` run on the branch (or `run_id`) against the changes since the last passing run, and
  publishes the review to https://flash-mx.github.io/dev/review/. Auth: the `ANTHROPIC_API_KEY`
  secret. Local run: `python3 .github/agent/tools/agent.py local --results <dir>`.
