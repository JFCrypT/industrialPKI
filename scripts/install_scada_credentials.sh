#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

BUNDLE="${1:-scada_credentials.tar.gz}"
[ -f "$BUNDLE" ] || { echo "Bundle not found: $BUNDLE" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

tar -xzf "$BUNDLE" -C "$TMP"
SRC="$TMP/scada_credentials"

mkdir -p pki/ca/certs pki/scada/certs pki/scada/private
install -m 0644 "$SRC/rootCA.crt" pki/ca/certs/rootCA.crt
install -m 0644 "$SRC/scada.crt" pki/scada/certs/scada.crt
install -m 0600 "$SRC/scada.key" pki/scada/private/scada.key

echo "SCADA credentials installed."
