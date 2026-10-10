# Dual SCADA — M262 + Delta

The SCADA operates two independent paths:

```text
M262 path   -> TLS/mTLS through the gateway on TCP/802
Delta path  -> standard plaintext Modbus/TCP
```

The current PoC encrypts only the SCADA-to-gateway segment. TLS terminates at the gateway.

---

## Configuration files

Two profiles are maintained:

```text
scada_dual_config_emulator.json
scada_dual_config_physical.json
```

The application always loads:

```text
scada_dual_config.json
```

For emulator testing:

```bash
cp scada/scada_dual_config_emulator.json \
   scada/scada_dual_config.json
```

For physical PLC testing:

```bash
cp scada/scada_dual_config_physical.json \
   scada/scada_dual_config.json
```

---

## Run

From the repository root:

```bash
source .venv/bin/activate
python scada/scada_dual_m262_delta.py
```

---

## TLS credentials

The M262 protected path uses:

```text
pki/ca/certs/rootCA.crt
pki/scada/certs/scada.crt
pki/scada/private/scada.key
```

The gateway authenticates the SCADA certificate against the CAETI Root CA.

---

## Validated emulator path

```text
SCADA -> 127.0.0.1:802 -> TLS gateway -> M262 emulator:1502
```

Delta:

```text
SCADA -> 127.0.0.1:1503 -> Delta emulator
```

---

## Screenshots

Connected protected path:

![SCADA connected through TLS](../docs/images/scada_tls_connected.png)

Gateway unavailable:

![SCADA with gateway offline](../docs/images/scada_gateway_offline.png)

The stable GUI is a laboratory control interface, not a full transport-health monitoring platform. A stale visual `CONNECTED` state may require an explicit reconnect or fresh operation after a gateway failure.

---

## Physical Delta mapping currently used

```text
Red          1281
Yellow       1282
Green        1283
START/STOP   1284
HACKED       1286
Emergency    pending physical confirmation
```

Physical Delta logic:

```text
START = 1
STOP  = 0
```

---

## End-to-end limitation

Current:

```text
SCADA == encrypted ==> Gateway -- plaintext Modbus --> M262
```

Target:

```text
SCADA ============== encrypted ==============> M262
```

The target depends strictly on verified native Modbus/TLS / Modbus Security support, or an equivalent TLS termination capability, on the physical M262.
