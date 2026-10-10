#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if ! python3 - <<'PY' >/dev/null 2>&1
import tkinter
PY
then
  echo "WARNING: tkinter is missing. Install it with: sudo apt install python3-tk"
fi

echo "Development environment ready."
echo "Python: $(.venv/bin/python --version)"
echo "PyModbus: $(.venv/bin/python -c 'import pymodbus; print(pymodbus.__version__)')"
