#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/vanveluwen/outbush-ai}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo on the Pi: sudo REPO_DIR=$REPO_DIR bash scripts/install_pi_services.sh" >&2
  exit 1
fi

install -m 0644 "$REPO_DIR/systemd/outbush-ai.service" /etc/systemd/system/outbush-ai.service

if [[ -f "$REPO_DIR/systemd/llama-server.service" ]]; then
  install -m 0644 "$REPO_DIR/systemd/llama-server.service" /etc/systemd/system/llama-server.service
fi

systemctl daemon-reload
if [[ -x /home/vanveluwen/llama-bin-b9616/llama-b9616/llama-server && -f /home/vanveluwen/models/qwen2.5-0.5b-instruct-q4_k_m.gguf ]]; then
  systemctl enable llama-server.service
else
  echo "Skipping llama-server enable: binary or model is missing."
fi
systemctl enable outbush-ai.service

echo "Installed outbush-ai.service."
echo "Start it with: sudo systemctl start outbush-ai"
echo "If llama-server prerequisites are present, llama-server.service was enabled too."
