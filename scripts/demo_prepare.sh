#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/select_emulator.sh
./scripts/bootstrap_dev.sh

for f in \
  pki/ca/certs/rootCA.crt \
  pki/gateway/certs/gateway.crt \
  pki/gateway/private/gateway.key \
  pki/scada/certs/scada.crt \
  pki/scada/private/scada.key; do
  if [ ! -f "$f" ]; then
    echo "Missing PKI file: $f" >&2
    echo "Generate PKI first: ./scripts/generate_pki.sh <gateway-ip>" >&2
    exit 1
  fi
done

echo "Emulator profile selected and environment prepared."
echo "Open three terminals and run:"
echo "  ./scripts/run_emulator.sh"
echo "  ./scripts/run_gateway.sh"
echo "  ./scripts/run_scada.sh"
