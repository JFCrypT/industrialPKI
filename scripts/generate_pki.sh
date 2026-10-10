#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

GATEWAY_IP="${1:-192.168.0.24}"

for f in \
  pki/ca/private/rootCA.key \
  pki/gateway/private/gateway.key \
  pki/scada/private/scada.key; do
  if [ -e "$f" ]; then
    echo "Refusing to overwrite existing PKI material: $f" >&2
    echo "Use scripts/regenerate_pki_caeti.sh if replacement is intentional." >&2
    exit 1
  fi
done

mkdir -p \
  pki/ca/private pki/ca/certs \
  pki/gateway/private pki/gateway/csr pki/gateway/certs \
  pki/scada/private pki/scada/csr pki/scada/certs

umask 077

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 \
  -out pki/ca/private/rootCA.key

openssl req -x509 -new -sha256 \
  -key pki/ca/private/rootCA.key \
  -days 3650 \
  -out pki/ca/certs/rootCA.crt \
  -subj "/C=AR/O=CAETI/OU=Industrial Security Lab/CN=CAETI Industrial Root CA"

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
  -out pki/gateway/private/gateway.key

openssl req -new \
  -key pki/gateway/private/gateway.key \
  -out pki/gateway/csr/gateway.csr \
  -subj "/C=AR/O=CAETI/OU=OT/CN=modbus-m262-gateway"

cat > pki/gateway/gateway.ext <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:modbus-m262-gateway,IP:127.0.0.1,IP:${GATEWAY_IP}
EOF

openssl x509 -req \
  -in pki/gateway/csr/gateway.csr \
  -CA pki/ca/certs/rootCA.crt \
  -CAkey pki/ca/private/rootCA.key \
  -CAcreateserial \
  -out pki/gateway/certs/gateway.crt \
  -days 825 -sha256 \
  -extfile pki/gateway/gateway.ext

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
  -out pki/scada/private/scada.key

openssl req -new \
  -key pki/scada/private/scada.key \
  -out pki/scada/csr/scada.csr \
  -subj "/C=AR/O=CAETI/OU=SCADA/CN=scada-testbed"

cat > pki/scada/scada.ext <<'EOF'
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
EOF

openssl x509 -req \
  -in pki/scada/csr/scada.csr \
  -CA pki/ca/certs/rootCA.crt \
  -CAkey pki/ca/private/rootCA.key \
  -CAcreateserial \
  -out pki/scada/certs/scada.crt \
  -days 825 -sha256 \
  -extfile pki/scada/scada.ext

chmod 600 \
  pki/ca/private/rootCA.key \
  pki/gateway/private/gateway.key \
  pki/scada/private/scada.key

openssl verify \
  -CAfile pki/ca/certs/rootCA.crt \
  pki/gateway/certs/gateway.crt \
  pki/scada/certs/scada.crt

echo
echo "Subjects:"
openssl x509 -in pki/ca/certs/rootCA.crt -noout -subject
openssl x509 -in pki/gateway/certs/gateway.crt -noout -subject
openssl x509 -in pki/scada/certs/scada.crt -noout -subject

echo
echo "PKI generated successfully for gateway IP ${GATEWAY_IP}."
