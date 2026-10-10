#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

required=(
  pki/ca/certs/rootCA.crt
  pki/gateway/certs/gateway.crt
  pki/gateway/private/gateway.key
  pki/scada/certs/scada.crt
  pki/scada/private/scada.key
)
for f in "${required[@]}"; do
  [ -f "$f" ] || { echo "Missing: $f" >&2; exit 1; }
done

rm -rf dist/gateway_credentials dist/scada_credentials
mkdir -p dist/gateway_credentials dist/scada_credentials

install -m 0644 pki/ca/certs/rootCA.crt dist/gateway_credentials/rootCA.crt
install -m 0644 pki/gateway/certs/gateway.crt dist/gateway_credentials/gateway.crt
install -m 0600 pki/gateway/private/gateway.key dist/gateway_credentials/gateway.key

install -m 0644 pki/ca/certs/rootCA.crt dist/scada_credentials/rootCA.crt
install -m 0644 pki/scada/certs/scada.crt dist/scada_credentials/scada.crt
install -m 0600 pki/scada/private/scada.key dist/scada_credentials/scada.key

( cd dist && tar -czf gateway_credentials.tar.gz gateway_credentials )
( cd dist && tar -czf scada_credentials.tar.gz scada_credentials )

chmod 600 dist/*_credentials.tar.gz

echo "Created:"
echo "  dist/gateway_credentials.tar.gz  -> Raspberry Pi / TLS gateway"
echo "  dist/scada_credentials.tar.gz    -> SCADA host"
echo
echo "IMPORTANT: rootCA.key is NOT included and must remain on the CA workstation."
echo "Transfer these bundles only over a trusted/encrypted channel or removable media."
