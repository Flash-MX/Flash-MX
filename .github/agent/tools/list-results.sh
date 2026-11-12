#!/usr/bin/env bash
set -euo pipefail
WORK="${1:-.test-analysis}"
find "$WORK/results" -type d -name '20*' 2>/dev/null | sort
