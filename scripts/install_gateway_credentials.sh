#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

BUNDLE="${1:-gateway_credentials.tar.gz}"
[ -f "$BUNDLE" ] || { echo "Bundle not found: $BUNDLE" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

tar -xzf "$BUNDLE" -C "$TMP"
SRC="$TMP/gateway_credentials"

mkdir -p pki/ca/certs pki/gateway/certs pki/gateway/private
install -m 0644 "$SRC/rootCA.crt" pki/ca/certs/rootCA.crt
install -m 0644 "$SRC/gateway.crt" pki/gateway/certs/gateway.crt
install -m 0600 "$SRC/gateway.key" pki/gateway/private/gateway.key

echo "Gateway credentials installed."
