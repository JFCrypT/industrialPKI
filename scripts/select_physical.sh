#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
cp .env.physical .env
cp scada/scada_dual_config_physical.json scada/scada_dual_config.json
echo "Physical PLC profile selected."
