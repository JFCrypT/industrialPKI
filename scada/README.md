# Dual SCADA — M262 + Delta

The SCADA uses two transports simultaneously:

- **M262 test path:** Modbus/TLS through the industrialPKI gateway on TCP/802.
- **Delta:** plain Modbus TCP.

The current local proof of concept validates TLS between the SCADA and the gateway. It does **not** yet prove end-to-end TLS termination inside the physical M262.

## Configuration profiles

Two profiles are provided:

- `scada_dual_config_emulator.json`
- `scada_dual_config_physical.json`

The application always loads:

```text
scada_dual_config.json
```

Select a profile by copying it to that filename, or use:

```bash
./scripts/select_profile.sh emulator
```

or:

```bash
./scripts/select_profile.sh physical
```

## Run

From the repository root:

```bash
source .venv/bin/activate
python scada/scada_dual_m262_delta.py
```

## Cryptographic parameters

The SCADA TLS client trusts `rootCA.crt`, presents the RSA-3072 `scada.crt` / `scada.key` identity, and enforces TLS 1.2 as the minimum protocol version. TLS 1.3 has been observed in the laboratory.

The exact symmetric cipher suite is negotiated by OpenSSL and is not pinned by the SCADA code.

See [`../docs/CRYPTOGRAPHIC_PROFILE.md`](../docs/CRYPTOGRAPHIC_PROFILE.md).

## M262 TLS client

The M262 client uses `ModbusTlsClient` with:

- Root CA: `pki/ca/certs/rootCA.crt`
- Client certificate: `pki/scada/certs/scada.crt`
- Client private key: `pki/scada/private/scada.key`

The M262 write path uses FC15 (`write_coils`) even for a single coil. Reads use FC01. Delta may use FC05.

### Validated emulator path

```text
SCADA -> 127.0.0.1:802 (mTLS) -> TLS gateway -> M262 emulator:1502
```

### Connected state

![SCADA connected through TLS](../docs/images/scada_tls_connected.png)

### Gateway failure behavior

When the TLS gateway is stopped, a new or repeated connection attempt to the M262 path fails:

![SCADA with TLS gateway offline](../docs/images/scada_gateway_offline.png)

This negative test demonstrates that the SCADA is not bypassing TLS and connecting directly to the M262 emulator. The stable GUI does not implement an automatic transport-health watchdog, so an already-open panel can retain a stale CONNECTED label until disconnect/reconnect or a fresh connection attempt.

## End-to-end limitation

The current gateway terminates TLS. Consequently, the gateway-to-backend Modbus segment is plaintext.

True end-to-end Modbus encryption requires the physical M262 to terminate TLS/mTLS itself. This depends strictly on M262 compatibility with native Modbus Security / Modbus-TLS or an equivalent programmable TLS server capability. Until that is verified, the project must describe the current implementation as **SCADA-to-gateway encrypted**, not SCADA-to-M262 end-to-end encrypted.

## Delta physical mapping currently used

- Y0 / red: `1281`
- Y1 / yellow: `1282`
- Y2 / green: `1283`
- Y3 / START/STOP: `1284`
- Y5 / HACKED: `1286`
- Emergency is intentionally left blank in the physical profile until the final ladder mapping is confirmed.

Physical Delta logic:

- START = `1`
- STOP = `0`
