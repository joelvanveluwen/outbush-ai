#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-vanveluwen-pi5}"
PORT="${PORT:-7862}"

ssh "vanveluwen@$HOST" "cd ~/outbush-ai && python3 -m unittest discover -s tests"
ssh "vanveluwen@$HOST" "cd ~/outbush-ai && . .venv/bin/activate && python scripts/pi_smoke_test.py http://127.0.0.1:$PORT"
python scripts/pi_smoke_test.py "http://$HOST:$PORT"
