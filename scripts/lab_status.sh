#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "=== Docker ==="
docker compose ps || true
echo
echo "=== Relevant listeners ==="
ss -ltnp 2>/dev/null | grep -E ':802|:1502|:1503|:502' || true
echo
echo "=== Active profiles ==="
echo ".env:"
cat .env 2>/dev/null || echo "(missing)"
echo
echo "SCADA M262/Delta endpoints:"
.venv/bin/python - <<'PY' 2>/dev/null || true
import json
from pathlib import Path
p=Path('scada/scada_dual_config.json')
if p.exists():
    d=json.loads(p.read_text())
    for k in ('m262','delta'):
        x=d[k]
        print(f"{k.upper()}: {x['ip']}:{x['port']} transport={x.get('transport','tcp')} unit={x['device_id']}")
else:
    print('(active SCADA config missing)')
PY
