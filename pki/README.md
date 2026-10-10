# PKI material

This directory intentionally contains **no operational credentials** in the public repository.

Generated/provisioned files are ignored by Git.

## CA workstation

The CA workstation may contain:

```text
pki/ca/private/rootCA.key      PRIVATE — never leave the CA workstation
pki/ca/certs/rootCA.crt        public trust anchor
```

## TLS gateway

The Raspberry Pi / gateway requires only:

```text
pki/ca/certs/rootCA.crt
pki/gateway/certs/gateway.crt
pki/gateway/private/gateway.key
```

It does **not** require `rootCA.key`.

## SCADA host

The SCADA host requires:

```text
pki/ca/certs/rootCA.crt
pki/scada/certs/scada.crt
pki/scada/private/scada.key
```

Use `scripts/export_credentials.sh` on the CA workstation to create separate gateway and SCADA deployment bundles. Transfer them only through a trusted/encrypted channel or controlled removable media.

## Field-test recommendation

For the Neuquén laboratory deployment, the simplest reproducible workflow is to generate/sign the PKI on the CA workstation and securely transfer only `gateway_credentials.tar.gz` to Jorge. The bundle contains `rootCA.crt`, `gateway.crt`, and `gateway.key`; it never contains `rootCA.key`.

Generating the gateway private key directly on the Raspberry and using a CSR is preferable for stronger key custody, but that CSR workflow is not the default automated path in this repository.

## Key-custody recommendation

For the fastest reproducible laboratory deployment, the CA workstation may generate the gateway key/certificate and export `gateway_credentials.tar.gz` for secure transfer to the Raspberry Pi.

For stronger field key custody, generate the gateway private key directly on the Raspberry Pi and send only a CSR to the CA workstation for signing. In both workflows, `rootCA.key` remains exclusively on the CA workstation and is never copied to the Raspberry Pi or SCADA host.
