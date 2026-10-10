#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

./scripts/select_physical.sh

for f in \
  pki/ca/certs/rootCA.crt \
  pki/gateway/certs/gateway.crt \
  pki/gateway/private/gateway.key; do
  [ -f "$f" ] || { echo "Missing gateway credential: $f" >&2; exit 1; }
done

docker compose up -d --build
docker compose ps

echo
echo "Physical gateway deployed."
echo "Backend from .env:"
cat .env
