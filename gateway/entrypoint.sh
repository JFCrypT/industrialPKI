#!/bin/sh
set -eu

: "${M262_IP:?M262_IP is required}"
: "${M262_PORT:?M262_PORT is required}"

sed -i \
  "s/M262_IP/${M262_IP}/g; s/M262_PORT/${M262_PORT}/g" \
  /etc/stunnel/stunnel.conf

exec stunnel /etc/stunnel/stunnel.conf
