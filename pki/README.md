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

For a remote laboratory deployment, the simplest reproducible workflow is to generate/sign the PKI on the CA workstation and securely transfer only the gateway credential bundle to the gateway host. The bundle contains `rootCA.crt`, `gateway.crt`, and `gateway.key`; it never contains `rootCA.key`.

Generating the gateway private key directly on the Raspberry and using a CSR is preferable for stronger key custody, but that CSR workflow is not the default automated path in this repository.

## Implemented cryptographic algorithms

```text
Root CA key             RSA 4096-bit
Gateway key             RSA 3072-bit
SCADA key               RSA 3072-bit
Certificate signatures  SHA-256 with RSA
Certificate format      X.509 v3
TLS minimum             TLS 1.2
Observed TLS            TLS 1.3
Authentication          mutual TLS (mTLS)
```

The exact symmetric TLS cipher suite is negotiated at runtime and is not currently pinned in project configuration.

See [`../docs/CRYPTOGRAPHIC_PROFILE.md`](../docs/CRYPTOGRAPHIC_PROFILE.md).
