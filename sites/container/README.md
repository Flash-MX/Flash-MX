## Containerized Flash-X testing (`container` site)

This site runs the Flash-X test suite with [`flashxtest`](https://github.com/Flash-X/Flash-X-Test)
inside a Docker container that has **AMReX** and **HYPRE** preinstalled. It is the
GitHub Actions counterpart to `sites/ganon_jenkins/` (which targets Jenkins).

### Layout

- `Makefile.h` — build configuration. Expects AMReX at `/home/lib/amrex/{1D,2D,3D}`
  and HYPRE at `/home/lib/hypre`, and uses the parallel HDF5 wrappers `h5pfc`/`h5pcc`.
- `Dockerfile` — one-time/cached image build: toolchain, MPI/HDF5, Bittree, AMReX,
  HYPRE, and `flashxtest`.
- `testsuites/*.suite` — test specifications (modeled on `tests/re3t/Tests.suite`),
  referencing test keys from each simulation's `tests/tests.toml`.

### Workflows

Defined in `.github/workflows/`:

- **`container-update-image.yml`** — builds the image and pushes it to
  `ghcr.io/<owner>/flashx-container:latest`. Runs on changes to `Dockerfile` or on
  manual dispatch (cached, so it rarely rebuilds).
- **`container-run.yml`** — on push/PR, runs `flashxtest init → setup-suite → run-suite`
  inside the image (repo mounted at `/home/mount/FlashX`, run as non-root user
  `flashx`, uid 1001), comparing against the baked-in benchmarks. Uploads
  `TestResults` as an artifact.
- **`container-update-benchmarks.yml`** — manual dispatch; regenerates benchmarks.

### Adding tests

Add lines to `testsuites/*.suite`. Each line names a setup under
`source/Simulation/SimulationMain` and a `-t` test key from that simulation's
`tests/tests.toml`. See the header comment in `testsuites/incompFlow.suite` for
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
