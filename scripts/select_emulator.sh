#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
cp .env.emulator .env
cp scada/scada_dual_config_emulator.json scada/scada_dual_config.json
echo "Emulator profile selected."
