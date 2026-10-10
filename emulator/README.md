# Dual PLC Emulator

This emulator provides two Modbus TCP servers for local SCADA/PKI testing.

## Endpoints

- M262 emulator: `0.0.0.0:1502`, Unit ID `255`
- Delta emulator: `0.0.0.0:1503`, Unit ID `1`

## Emulator addresses

### M262

- START/STOP: `100`
- EMERGENCY: `101`
- HACKED: `102`
- RED: `110`
- YELLOW: `111`
- GREEN: `112`

### Delta

- START/STOP: `3120`
- EMERGENCY: `3121`
- HACKED: `3122`
- RED: `3130`
- YELLOW: `3131`
- GREEN: `3132`

## Behavior

Normal cycle: 8 s green, 2 s green+yellow, 8 s red, 2 s red+yellow.

Emergency mode: red flashes 1 s ON / 1 s OFF.

Hacked mode: rapid 200 ms output sequence.

Run from the repository root:

```bash
source .venv/bin/activate
python emulator/plc_emulator.py
```
