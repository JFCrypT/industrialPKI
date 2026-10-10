#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d --build
echo "Gateway started. Streaming logs (Ctrl+C stops log view only)..."
exec docker compose logs -f
