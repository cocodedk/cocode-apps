#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest -q
if command -v ruff >/dev/null 2>&1; then ruff check tools tests; fi
