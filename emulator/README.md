# Dual PLC Emulator

The emulator provides two plaintext Modbus/TCP servers for local testing.

It does not implement PKI or TLS itself.

TLS is provided by the external gateway in front of the M262 emulator.

---

## Endpoints

```text
M262 emulator   0.0.0.0:1502   Unit ID 255
Delta emulator  0.0.0.0:1503   Unit ID 1
```

The non-standard laboratory ports intentionally distinguish emulation from physical Modbus/TCP on TCP/502.

---

## M262 addresses

```text
START/STOP   100
EMERGENCY    101
HACKED       102
RED          110
YELLOW       111
GREEN        112
```

## Delta addresses

```text
START/STOP   3120
EMERGENCY    3121
HACKED       3122
RED          3130
YELLOW       3131
GREEN        3132
```

---

## Run

From the repository root:

```bash
source .venv/bin/activate
python emulator/plc_emulator.py
```

The M262 emulator is reached through:

```text
SCADA -> TLS gateway:802 -> emulator:1502
```

The Delta emulator is reached directly through:

```text
SCADA -> emulator:1503
```
