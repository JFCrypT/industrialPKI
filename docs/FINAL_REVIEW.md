# Final Review Status

This repository was reviewed for the laboratory release of `industrialPKI`.

## Static validation performed

- Python files compile successfully.
- SCADA JSON profiles parse successfully.
- Shell scripts pass `bash -n` syntax checks.
- CAETI naming is used consistently.
- Emulator and physical profiles remain separate.
- Docker gateway configuration fails fast when `M262_IP` or `M262_PORT` is missing.
- Active `.env`, active SCADA config, private keys, CSRs and operational certificates are excluded from the public repository bundle.

Run the local audit at any time with:

```bash
python3 -m compileall -q scada emulator
python3 -m json.tool scada/scada_dual_config_emulator.json >/dev/null
python3 -m json.tool scada/scada_dual_config_physical.json >/dev/null
for script in scripts/*.sh; do bash -n "$script" || exit 1; done
```

## Validated laboratory scope

```text
SCADA == mTLS/TCP 802 ==> TLS gateway -- plaintext Modbus/TCP 1502 --> M262 emulator
SCADA ------------------------------ plaintext Modbus/TCP 1503 --> Delta emulator
```

The current proof of concept validates PKI, mutual TLS and encrypted SCADA-to-gateway transport. It does **not** prove end-to-end encryption to a physical M262.

## Physical decision point

End-to-end protection is possible only if the physical M262 can terminate TLS/mTLS itself, through native Modbus Security/Modbus-TLS or an equivalent controller-side TLS server capability. If TLS terminates on the Raspberry gateway, the Raspberry-to-M262 TCP/502 segment remains plaintext.

## Credential custody

Preferred field practice: keep `rootCA.key` only on the CA workstation. For the simplest laboratory deployment, securely transfer `gateway_credentials.tar.gz` to the Raspberry Pi. A stronger future workflow is to generate `gateway.key` directly on the Raspberry and transfer only a CSR to the CA workstation for signing.
