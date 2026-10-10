#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

BUNDLE="${1:-}"
M262_IP_OVERRIDE="${2:-}"
M262_PORT_OVERRIDE="${3:-502}"

if [ -z "$BUNDLE" ]; then
  echo "Usage: $0 /path/to/gateway_credentials.tar.gz [m262-ip] [m262-port]" >&2
  exit 1
fi

command -v docker >/dev/null 2>&1 || { echo "Docker is not installed." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose plugin is unavailable." >&2; exit 1; }

./scripts/install_gateway_credentials.sh "$BUNDLE"
cp .env.physical .env

if [ -n "$M262_IP_OVERRIDE" ]; then
  cat > .env <<EOF2
M262_IP=${M262_IP_OVERRIDE}
M262_PORT=${M262_PORT_OVERRIDE}
EOF2
fi

echo "Active physical backend:"
cat .env

docker compose up -d --build
docker compose ps

echo
echo "Raspberry gateway provisioned."
echo "Logs: docker compose logs -f"
