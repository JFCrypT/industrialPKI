#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PROFILE="${1:-}"

case "$PROFILE" in
    emulator)
        cp .env.emulator .env
        cp scada/scada_dual_config_emulator.json \
           scada/scada_dual_config.json
        ;;
    physical)
        cp .env.physical .env
        cp scada/scada_dual_config_physical.json \
           scada/scada_dual_config.json
        ;;
    *)
        echo "Usage: $0 {emulator|physical}"
        exit 1
        ;;
esac

echo "Active profile: $PROFILE"
