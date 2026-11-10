## GitHub workflows

These workflows run the Flash-X test suite with [`flashxtest`](https://github.com/Flash-X/Flash-X-Test)
inside a Docker container that has AMReX and HYPRE preinstalled, using the
`sites/container` configuration. See `sites/container/README.md` for details.

- **`container-update-image.yml`** — build and publish the test image to GHCR.
- **`container-run.yml`** — run the suite on push/PR and compare against baked-in benchmarks.
- **`container-update-benchmarks.yml`** — regenerate and package benchmarks (manual dispatch).
