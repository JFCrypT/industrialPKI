#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/6] Python syntax"
python3 -m py_compile \
  scada/scada_dual_m262_delta.py \
  emulator/plc_emulator.py \
  attack/modifPLC.py

echo "[2/6] JSON profiles"
python3 - <<'PY'
import json
from pathlib import Path
for p in sorted(Path('scada').glob('*.json')):
    json.loads(p.read_text(encoding='utf-8'))
    print(f'  OK {p}')
PY

echo "[3/6] Shell syntax"
for f in scripts/*.sh gateway/entrypoint.sh; do
  bash -n "$f"
done

echo "[4/6] CAETI naming"
if grep -Rni --exclude-dir=.git --exclude='*.png' 'CYBER\.AR' README.md docs scada emulator pki gateway scripts 2>/dev/null; then
  echo "ERROR: legacy CYBER.AR identity found." >&2
  exit 1
fi

echo "[5/6] Secret scan"
if find . -type f \( -name '*.key' -o -name '*.csr' -o -name '*.srl' \) | grep -q .; then
  echo "WARNING: operational PKI material is present in the working tree."
  find . -type f \( -name '*.key' -o -name '*.csr' -o -name '*.srl' \)
else
  echo "  No private keys/CSRs/serial files in repository tree."
fi

echo "[6/6] Docker Compose"
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  if [ -f .env ]; then
    docker compose config >/dev/null
    echo "  Compose configuration OK."
  else
    echo "  Skipped compose expansion: .env is intentionally absent. Select a profile first."
  fi
else
  echo "  Docker/Compose unavailable; static checks completed."
fi

echo "Project checks completed."
