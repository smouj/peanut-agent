#!/usr/bin/env bash
set -euo pipefail

# 🥜 PEANUT-AGENT — 1-command installer (Linux/macOS)
# - Creates/uses .venv
# - Installs deps
# - Launches the Wizard

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PY_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PY_BIN="python"
else
  echo "❌ No encuentro Python. Instala Python 3.10+ y reintenta." >&2
  exit 1
fi

"$PY_BIN" wizard.py
