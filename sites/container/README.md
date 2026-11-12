## Containerized Flash-X testing (`container` site)

This site runs the Flash-X test suite with [`flashxtest`](https://github.com/Flash-X/Flash-X-Test)
inside a Docker container that has **AMReX** and **HYPRE** preinstalled, on GitHub Actions.

### Layout

- `Makefile.h` — build configuration. Expects AMReX at `/home/lib/amrex/{1D,2D,3D}`
  and HYPRE at `/home/lib/hypre`, and uses the parallel HDF5 wrappers `h5pfc`/`h5pcc`.
- `Dockerfile` — one-time/cached image build: toolchain, MPI/HDF5, Bittree, AMReX,
  HYPRE, and `flashxtest`.
- `testsuites/*.suite` — test specifications (modeled on `tests/re3t/Tests.suite`),
  referencing test keys from each simulation's `tests/tests.yaml`.

### Workflows

Defined in `.github/workflows/`:

- **`container-update-image.yml`** — builds the image and pushes it to
  `ghcr.io/<owner>/flashx-container:latest`. Runs on changes to `Dockerfile` or on
  manual dispatch (cached, so it rarely rebuilds).
- **`container-run.yml`** — on push to `main`/`staged` (or manual dispatch), runs
  `flashxtest init → run-suite` for each `testsuites/*.suite` inside the image
  (repo mounted at `/home/mount/FlashX`, run as non-root user `flashx`, uid 1001),
  comparing against the downloaded benchmarks. Uploads a `TestResults-<suite>`
  artifact per suite, then publishes a merged webview to
  **https://flash-mx.github.io/dev** (see below).
- **`container-update-benchmarks.yml`** — manual dispatch; regenerates benchmarks.

### Viewing results

Published results: **https://flash-mx.github.io/dev**. Only the lightweight
webview (logs, comparison output, `summary.json`) is pushed to the `dev-results`
branch of [Flash-MX/flash-mx.github.io](https://github.com/Flash-MX/flash-mx.github.io).
The large outputs (`flash_output`, HDF5 checkpoint/plot files, build directories)
stay in the workflow's `TestResults-<suite>` artifacts.

To connect the two, the `publish-website` job writes a `run.json` into each
published run with the following fields:

```json
{
  "run_url": "https://github.com/<owner>/<repo>/actions/runs/<run_id>",
  "commit": "<sha>", "commit_url": "...", "ref": "main",
  "artifacts": [
    {"name": "TestResults-incomp", "size_in_bytes": 123456789,
     "expires_at": "2027-02-08T00:00:00Z",
     "url": "https://github.com/<owner>/<repo>/actions/runs/<run_id>/artifacts/<id>"}
  ]
}
```

`.github/workflows/pages.py (dev subcommand)` uses it to add a commit link, a workflow-run link,
and a "Full outputs" list of artifact download links to each run on the Dev page.
`run.json` moves with a run when it is kept as the last passing run, so its links
always point to the run that produced those results. Notes:

- Downloading artifacts requires being signed in to GitHub with read access to the repo.
- Artifacts expire after the repository's retention period (Settings → Actions →
  General → Artifact and log retention; default 90 days). Expired links are shown
  as expired rather than as broken links. To keep a particular run's outputs, download
  the artifact before then (or raise `retention-days` on the upload step).

### Adding tests

Add lines to `testsuites/*.suite`. Each line names a setup under
`source/Simulation/SimulationMain` and a `-t` test key from that simulation's
`tests/tests.yaml`. See the header comment in `testsuites/incomp.suite` for
the full option list. Comparison/Composite tests need a `-cbase` (and `-rbase`)
date that matches a baseline in the image archive.

### Using benchmarks

Comparison (`-cbase`) and Composite (`-cbase`/`-rbase`) tests compare against an
approved baseline. At runtime, `container-run.yml` downloads every URL listed in the
`BENCHMARK_ARCHIVE_URLS` Actions variable into `LocalArchive/`; each archive
extracts to `LocalArchive/<date>/...`. The `<date>` in the suite files' `-cbase`/
`-rbase` tags must match a downloaded archive.

### Updating benchmarks

1. Run the **`container-update-benchmarks`** workflow (Actions → Run workflow). Optionally
   pass a `benchmark_date`; it defaults to today. It will:
   - run the suite with `--archive` to generate fresh baselines,
   - restamp the suite files' `-cbase`/`-rbase` with the new date,
   - upload the baseline as artifact `flashx-benchmarks-<date>.tar.gz`,
   - open a PR with the restamped suite files.
2. Download the tarball artifact and publish it (e.g. to Box); copy its static URL.
3. Go to Settings → Secrets and variables → Actions → Variables →
   `BENCHMARK_ARCHIVE_URLS` → Edit. Add the new URL on a new line at the bottom,
   then save. Keep all prior URLs — each suite references its own `-cbase`/`-rbase`
   date and needs the matching archive available at runtime.
4. Merge the auto-opened PR. No image rebuild required; `container-run.yml` downloads
   all listed archives into `LocalArchive/` at runtime.
