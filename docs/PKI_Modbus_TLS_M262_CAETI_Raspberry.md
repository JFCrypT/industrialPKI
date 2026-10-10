# Raspberry Pi TLS Gateway — Straightforward Deployment Guide

This guide deploys the current `industrialPKI` TLS gateway on a Raspberry Pi with the minimum number of steps.

> The Raspberry Pi terminates TLS. The final Raspberry Pi -> M262 connection is standard plaintext Modbus/TCP.
>
> True end-to-end encryption requires native Modbus/TLS compatibility on the M262 itself and is a separate physical-validation phase.

---

## 1. Required equipment

```text
SCADA host
Raspberry Pi gateway
Schneider M262
Ethernet/Wi-Fi network as appropriate for the testbed
```

Current physical addressing plan:

```text
TLS gateway           192.168.0.24
M262 backend           192.168.0.25:502
Delta                  192.168.0.15:502
TLS service            TCP/802
```

Adjust addresses if the field network differs.

---

## 2. Before field deployment — CA workstation

Clone/open the repository:

```bash
cd ~/Documents/Proyectos/industrialPKI
```

Generate the PKI with the Raspberry Pi gateway IP:

```bash
./scripts/generate_pki.sh 192.168.0.24
```

Verify:

```bash
openssl verify \
  -CAfile pki/ca/certs/rootCA.crt \
  pki/gateway/certs/gateway.crt \
  pki/scada/certs/scada.crt
```

Export deployment credentials:

```bash
./scripts/export_credentials.sh
```

This creates:

```text
dist/gateway_credentials.tar.gz
dist/scada_credentials.tar.gz
```

### Credential rule

Transfer to the Raspberry Pi:

```text
gateway_credentials.tar.gz
```

Do not transfer:

```text
rootCA.key
```

`rootCA.key` remains only on the CA workstation.

The default PoC workflow transports the gateway private key inside the protected gateway bundle for simplicity.

For stronger future key custody, generate the gateway private key directly on the Raspberry Pi and sign only its CSR on the CA workstation.

---

## 3. Raspberry Pi — first installation

Clone the project:

```bash
git clone https://github.com/JFCrypT/industrialPKI.git
cd industrialPKI
```

Install Docker and Docker Compose:

```bash
./scripts/bootstrap_raspberry_gateway.sh
```

If requested by the script, log out and back in once.

Verify:

```bash
docker --version
docker compose version
```

---

## 4. Copy the gateway bundle to the Raspberry Pi

Use a trusted administrative method such as SSH/SCP, SFTP or controlled removable media.

Example from the administrative workstation:

```bash
scp dist/gateway_credentials.tar.gz <raspberry-user>@192.168.0.24:~/
```

---

## 5. Install the credentials on the Raspberry Pi

From the Raspberry Pi:

```bash
cd ~/industrialPKI

mkdir -p pki/ca/certs pki/gateway/certs pki/gateway/private

tmpdir="$(mktemp -d)"
tar -xzf ~/gateway_credentials.tar.gz -C "$tmpdir"

install -m 0644 "$tmpdir/gateway_credentials/rootCA.crt" \
  pki/ca/certs/rootCA.crt

install -m 0644 "$tmpdir/gateway_credentials/gateway.crt" \
  pki/gateway/certs/gateway.crt

install -m 0600 "$tmpdir/gateway_credentials/gateway.key" \
  pki/gateway/private/gateway.key

rm -rf "$tmpdir"
```

Verify:

```bash
ls -l \
  pki/ca/certs/rootCA.crt \
  pki/gateway/certs/gateway.crt \
  pki/gateway/private/gateway.key
```

---

## 6. Configure the physical M262 backend

Copy the physical backend profile:

```bash
cp .env.physical .env
```

Verify:

```bash
cat .env
```

Expected:

```text
M262_IP=192.168.0.25
M262_PORT=502
```

If the field M262 uses another address, edit `.env`:

```bash
nano .env
```

---

## 7. Start the gateway

```bash
docker compose up -d --build
```

Check:

```bash
docker compose ps
```

Follow logs:

```bash
docker compose logs -f
```

Expected startup:

```text
Configuration successful
```

Expected successful SCADA authentication:

```text
Certificate accepted at depth=0: C=AR, O=CAETI, OU=SCADA, CN=scada-testbed
```

Expected physical backend connection:

```text
s_connect: connected 192.168.0.25:502
```

---

## 8. Configure the SCADA host for physical operation

The SCADA host requires:

```text
rootCA.crt
scada.crt
scada.key
```

Install them under:

```text
pki/ca/certs/rootCA.crt
pki/scada/certs/scada.crt
pki/scada/private/scada.key
```

Select the physical SCADA profile:

```bash
cp scada/scada_dual_config_physical.json \
   scada/scada_dual_config.json
```

The physical profile should point the M262 client to the Raspberry Pi TLS gateway:

```text
Gateway IP   192.168.0.24
Gateway port 802
transport    TLS
```

Delta remains direct Modbus/TCP to its physical PLC.

Run:

```bash
source .venv/bin/activate
python scada/scada_dual_m262_delta.py
```

---

## 9. Validate

### Gateway listener

On the Raspberry Pi:

```bash
ss -ltn | grep ':802'
```

Expected listener on TCP/802.

### SCADA connection

Connect the M262 from the SCADA.

Gateway log should show:

```text
Certificate accepted at depth=0: C=AR, O=CAETI, OU=SCADA, CN=scada-testbed
s_connect: connected 192.168.0.25:502
```

### Wireshark

On the protected side:

```text
tcp.port == 802
```

Expected TLS encrypted application data.

On the Raspberry Pi-to-M262 side:

```text
tcp.port == 502
```

Expected standard plaintext Modbus/TCP.

This is expected behavior for the current gateway architecture.

---

## 10. Stop / restart

Stop:

```bash
docker compose down
```

Start:

```bash
docker compose up -d
```

Logs:

```bash
docker compose logs -f
```

---

## 11. End-to-end limitation

Current physical gateway topology:

```text
SCADA ===== encrypted mTLS / 802 =====> Raspberry Pi
                                       |
                                       | plaintext Modbus/TCP / 502
                                       v
                                      M262
```

This is not end-to-end encrypted to the PLC.

True E2E protection requires:

```text
SCADA ===== native Modbus/TLS + mTLS =====> M262
```

That depends strictly on verified M262 Modbus/TLS compatibility or an equivalent TLS termination capability on the PLC.

Do not claim end-to-end M262 encryption until that physical capability is experimentally confirmed.
