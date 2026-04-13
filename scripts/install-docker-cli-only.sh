#!/usr/bin/env bash
# Run with: sudo bash scripts/install-docker-cli-only.sh
# Purges Docker Desktop and installs Docker Engine (daemon) + same CLI plugins you had.
set -euo pipefail

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Run with: sudo bash $(basename "$0")" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get purge -y docker-desktop || true
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker

# Prefer local engine instead of Docker Desktop context
if docker context ls 2>/dev/null | grep -q 'default'; then
  docker context use default
fi
docker context rm desktop-linux 2>/dev/null || true

TARGET_USER="${SUDO_USER:-${USER:-luiz}}"
if id "$TARGET_USER" &>/dev/null; then
  usermod -aG docker "$TARGET_USER"
  echo "Added user '$TARGET_USER' to group docker."
fi

echo
echo "Done. Docker Engine is running (systemd: docker.service)."
echo "Open a new shell (or run: newgrp docker) so group membership applies, then: docker run hello-world"
echo "If 'docker context' still shows desktop-linux, run: docker context use default"
