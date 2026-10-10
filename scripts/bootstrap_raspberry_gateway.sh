#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this script as the normal user; it will call sudo when required." >&2
  exit 1
fi

. /etc/os-release
ARCH="$(dpkg --print-architecture)"

sudo apt-get update
sudo apt-get install -y ca-certificates curl git openssl netcat-openbsd
sudo install -m 0755 -d /etc/apt/keyrings

case "${ID:-}" in
  raspbian)
    if [ "$ARCH" = "arm64" ]; then
      # Docker currently directs 64-bit Raspberry Pi OS users to Debian arm64 packages.
      BASE_URL="https://download.docker.com/linux/debian"
    else
      BASE_URL="https://download.docker.com/linux/raspbian"
    fi
    SUITE="${VERSION_CODENAME}"
    ;;
  debian)
    BASE_URL="https://download.docker.com/linux/debian"
    SUITE="${VERSION_CODENAME}"
    ;;
  ubuntu)
    BASE_URL="https://download.docker.com/linux/ubuntu"
    SUITE="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
    ;;
  *)
    echo "Unsupported automatic Docker repository setup for ID=${ID:-unknown}." >&2
    echo "Install Docker Engine + Compose plugin manually, then rerun deployment." >&2
    exit 1
    ;;
esac

sudo curl -fsSL "${BASE_URL}/gpg" -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF2
Types: deb
URIs: ${BASE_URL}
Suites: ${SUITE}
Components: stable
Architectures: ${ARCH}
Signed-By: /etc/apt/keyrings/docker.asc
EOF2

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

echo
echo "Docker installed."
echo "Log out and back in once so group membership takes effect."
echo "Then verify: docker --version && docker compose version"
