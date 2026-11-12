# Agent tools

Small, focused helpers the test-analysis agent can invoke via `Bash`. Each
script is self-contained, takes its inputs as positional args, and prints to
stdout. The agent should prefer these over ad-hoc shell pipelines.

- `diff-stat.sh [BASE] [SHA]` — changed-file summary between two refs (defaults: $BASE/$SHA env or HEAD).
- `list-results.sh [WORK]` — list FlashTest result directories under $WORK/results.
- `find-tests.sh <setup>` — locate tests.yaml for a Simulation setup.
