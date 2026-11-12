#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-${BASE:-}}"
SHA="${2:-${SHA:-HEAD}}"
if [ -z "$BASE" ]; then
  echo "BASE not set" >&2
  exit 1
fi
git diff --stat "$BASE".."$SHA"
