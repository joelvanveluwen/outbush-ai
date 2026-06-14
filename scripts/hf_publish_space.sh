#!/usr/bin/env bash
set -euo pipefail

SPACE_ID="${SPACE_ID:?Set SPACE_ID, for example: SPACE_ID=yourname/outbush-ai}"

hf auth whoami >/dev/null

hf upload "$SPACE_ID" . --type space \
  --exclude ".git/*" \
  --exclude ".venv/*" \
  --exclude "__pycache__/*" \
  --exclude "*.pyc" \
  --commit-message "Publish Outbush AI Space"

echo "Uploaded Space files to $SPACE_ID"
