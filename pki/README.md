# PKI Material

The public repository must contain no operational private keys.

---

## CA workstation

```text
pki/ca/private/rootCA.key
pki/ca/certs/rootCA.crt
```

`rootCA.key` is the most sensitive asset in the project.

It must:

- remain on the trusted CA workstation;
- never be committed to Git;
- never be copied to the Raspberry Pi gateway;
- never be copied to the SCADA host.

---

## TLS gateway credentials

```text
rootCA.crt
gateway.crt
gateway.key
```

For the current PoC, these files are exported as:

```text
dist/gateway_credentials.tar.gz
```

and transferred through a trusted administrative channel.

---

## SCADA credentials

```text
rootCA.crt
scada.crt
scada.key
```

For deployment they are exported as:

```text
dist/scada_credentials.tar.gz
```

---

## Generate

```bash
./scripts/generate_pki.sh <gateway-ip>
```

Example:

```bash
./scripts/generate_pki.sh 192.168.0.24
```

## Export

```bash
./scripts/export_credentials.sh
```

---

## Key-custody note

The default PoC workflow generates the gateway private key on the CA/development workstation and transfers it inside the protected gateway bundle.

For stronger production key custody, a future hardening workflow should generate `gateway.key` directly on the Raspberry Pi and send only a CSR to the CA workstation for signing.

That stronger CSR model is optional and is not required for the current laboratory PoC.
