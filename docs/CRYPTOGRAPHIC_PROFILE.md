# Cryptographic Profile

This document records the cryptographic algorithms and parameters that are **actually implemented by the current `industrialPKI` PoC**.

It intentionally distinguishes the PKI algorithms from the TLS session algorithms.

## 1. PKI algorithms

| Component | Implemented algorithm / parameter |
|---|---|
| Certificate format | X.509 v3 |
| Root CA private/public key | RSA, 4096 bits |
| Gateway private/public key | RSA, 3072 bits |
| SCADA private/public key | RSA, 3072 bits |
| Certificate signature algorithm | SHA-256 with RSA (`sha256WithRSAEncryption`) |
| Root CA role | `CA:TRUE` |
| Gateway certificate EKU | TLS Web Server Authentication (`serverAuth`) |
| SCADA certificate EKU | TLS Web Client Authentication (`clientAuth`) |
| Gateway / SCADA key usage | Digital Signature, Key Encipherment |
| Root CA validity | 3650 days |
| Gateway / SCADA certificate validity | 825 days |

These parameters come directly from `scripts/generate_pki.sh` and from the generated certificates.

## 2. TLS / mTLS profile

The protected SCADA-to-gateway channel is configured as follows:

| Property | Current implementation |
|---|---|
| Transport security | TLS with mutual certificate authentication (mTLS) |
| Secure port | TCP/802 |
| Minimum TLS version | TLS 1.2 |
| Experimentally observed version | TLS 1.3 |
| Gateway authentication | X.509 certificate signed by CAETI Root CA |
| SCADA authentication | X.509 client certificate signed by CAETI Root CA |
| Gateway certificate validation | `verifyChain = yes`, `requireCert = yes` |
| SCADA trust anchor | `rootCA.crt` |
| Gateway trust anchor | `rootCA.crt` |

The SCADA code sets:

```python
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
```

The gateway sets:

```text
sslVersionMin = TLSv1.2
verifyChain = yes
requireCert = yes
```

## 3. Symmetric encryption and key exchange

The current PoC **does not hard-code a TLS cipher suite or key-exchange group**.

The exact session algorithms are negotiated by the TLS implementations provided by Python/OpenSSL and stunnel/OpenSSL.

Therefore the repository must not claim a fixed data-plane algorithm such as `AES-256-GCM`, `AES-128-GCM`, `ChaCha20-Poly1305`, or a specific ECDHE group unless it is explicitly configured or experimentally captured.

The laboratory has already observed TLS 1.3. In a TLS 1.3 session, the negotiated cipher suite is an AEAD suite and the handshake uses the TLS 1.3 key-establishment mechanism, but the exact cipher suite and named group remain session-negotiated in the present configuration.

To record the exact negotiated session parameters, use:

```bash
openssl s_client \
  -connect 127.0.0.1:802 \
  -cert pki/scada/certs/scada.crt \
  -key pki/scada/private/scada.key \
  -CAfile pki/ca/certs/rootCA.crt \
  -brief
```

Record at least:

```text
Protocol version
Ciphersuite
Peer certificate
Signature type
Server Temp Key / negotiated group
```

Wireshark can also be used to document the negotiated TLS version and cipher suite during the handshake.

## 4. What each algorithm does

```text
RSA-4096
  -> Root CA key pair
  -> anchors the PKI trust hierarchy

RSA-3072
  -> Gateway and SCADA identity key pairs

SHA-256 + RSA
  -> digital signatures on X.509 certificates

TLS 1.2 minimum / TLS 1.3 observed
  -> secure transport framework

Negotiated TLS session cipher
  -> symmetric encryption and integrity protection of Modbus application data in transit

X.509 + mTLS
  -> mutual authentication of SCADA and gateway
```

The certificates do **not** encrypt every Modbus packet directly with RSA. TLS uses the certificate identities during authentication and session establishment, then protects application traffic with negotiated symmetric session keys.

## 5. Current cryptographic boundary

The algorithms above currently protect:

```text
SCADA ===== TLS/mTLS =====> Gateway
```

They do not currently protect the final backend hop:

```text
Gateway ----- plaintext Modbus/TCP -----> M262
```

True end-to-end Modbus confidentiality requires the physical M262 itself to terminate compatible Modbus/TLS / mTLS.

## 6. Verification commands

Inspect the Root CA:

```bash
openssl x509 -in pki/ca/certs/rootCA.crt -noout -text
```

Inspect the gateway certificate:

```bash
openssl x509 -in pki/gateway/certs/gateway.crt -noout -text
```

Inspect the SCADA certificate:

```bash
openssl x509 -in pki/scada/certs/scada.crt -noout -text
```

Current generated certificates verify as:

```text
Root CA:  X.509 v3, RSA 4096, sha256WithRSAEncryption
Gateway:  X.509 v3, RSA 3072, sha256WithRSAEncryption
SCADA:    X.509 v3, RSA 3072, sha256WithRSAEncryption
```
