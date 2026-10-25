#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 harness/run.py 001 submissions/baseline.py "$@"
