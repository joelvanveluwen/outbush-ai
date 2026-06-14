#!/usr/bin/env bash
set -euo pipefail

SPACE_ID="${SPACE_ID:-build-small-hackathon/outbush-ai}"

hf auth whoami >/dev/null

hf upload "$SPACE_ID" . --type space \
  --exclude ".git/*" \
  --exclude ".venv/*" \
  --exclude ".modal/*" \
  --exclude ".secrets" \
  --exclude ".agents/*" \
  --exclude "__pycache__/*" \
  --exclude "*.pyc" \
  --commit-message "Publish Outbush AI Space"

echo "Uploaded Space files to $SPACE_ID"
