## GitHub workflows

These workflows run the Flash-X test suite with [`flashxtest`](https://github.com/Flash-X/Flash-X-Test)
inside a Docker container that has AMReX and HYPRE preinstalled, using the
`sites/container` configuration. See `sites/container/README.md` for details.

- **`container-update-image.yml`** — build and publish the test image to GHCR (on push to
  `main`/`staged` that changes `sites/container/Dockerfile`, or manual dispatch).
- **`container-run.yml`** — run the suite on push to `main`/`staged` (after waiting for any
  in-progress image build), compare against benchmarks,
  and publish results to https://flash-mx.github.io/dev, with links back to the run's
  `TestResults-*` artifacts (`flash_output`, HDF5 files, ...).
- **`container-update-benchmarks.yml`** — regenerate and package benchmarks (manual dispatch).
