#!/usr/bin/env bash
set -euo pipefail
setup="${1:?setup name required}"
find source/Simulation/SimulationMain -type f -path "*/$setup/tests/tests.yaml" 2>/dev/null
