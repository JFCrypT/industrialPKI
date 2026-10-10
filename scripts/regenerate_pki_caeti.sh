#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

GATEWAY_IP="${1:-192.168.0.24}"
BACKUP_DIR="pki_backup_$(date +%Y%m%d_%H%M%S)"

if [ -d pki ]; then
  cp -a pki "$BACKUP_DIR"
  echo "Backup created: $BACKUP_DIR"
fi

rm -f \
  pki/ca/private/rootCA.key \
  pki/ca/certs/rootCA.crt \
  pki/ca/certs/rootCA.srl \
  pki/gateway/private/gateway.key \
  pki/gateway/csr/gateway.csr \
  pki/gateway/certs/gateway.crt \
  pki/scada/private/scada.key \
  pki/scada/csr/scada.csr \
  pki/scada/certs/scada.crt

./scripts/generate_pki.sh "$GATEWAY_IP"

echo "Restart the gateway so it reloads the new credentials:"
echo "  docker compose down"
echo "  docker compose up -d --build"
