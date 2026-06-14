#!/usr/bin/env bash
set -euo pipefail

python -m modal setup --help >/dev/null
modal run modal_jobs/outbush_lora_smoke.py
