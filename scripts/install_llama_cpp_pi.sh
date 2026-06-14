#!/usr/bin/env bash
set -euo pipefail

LLAMA_TAG="${LLAMA_TAG:-b9616}"
LLAMA_DIR="${LLAMA_DIR:-/home/vanveluwen/llama-bin-$LLAMA_TAG}"
MODEL_REPO="${MODEL_REPO:-Qwen/Qwen2.5-0.5B-Instruct-GGUF}"
MODEL_FILE="${MODEL_FILE:-qwen2.5-0.5b-instruct-q4_k_m.gguf}"
MODEL_DIR="${MODEL_DIR:-/home/vanveluwen/models}"

mkdir -p "$LLAMA_DIR" "$MODEL_DIR"

cd "$LLAMA_DIR"
ARCHIVE="llama-${LLAMA_TAG}-bin-ubuntu-arm64.tar.gz"
if [[ ! -f "$ARCHIVE" ]]; then
  wget "https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_TAG}/${ARCHIVE}"
fi
tar -xzf "$ARCHIVE"

if [[ ! -x "$LLAMA_DIR/llama-$LLAMA_TAG/llama-server" ]]; then
  echo "Expected llama-server at $LLAMA_DIR/llama-$LLAMA_TAG/llama-server" >&2
  exit 1
fi

if [[ ! -f "$MODEL_DIR/$MODEL_FILE" ]]; then
  cd /home/vanveluwen/outbush-ai
  . .venv/bin/activate
  hf download "$MODEL_REPO" "$MODEL_FILE" --local-dir "$MODEL_DIR"
fi

"$LLAMA_DIR/llama-$LLAMA_TAG/llama-server" --version
ls -lh "$MODEL_DIR/$MODEL_FILE"

cat <<MSG
llama.cpp runtime is installed.

Binary:
  $LLAMA_DIR/llama-$LLAMA_TAG/llama-server

Model:
  $MODEL_DIR/$MODEL_FILE

Next:
  sudo bash /home/vanveluwen/outbush-ai/scripts/install_pi_services.sh
  sudo systemctl restart llama-server outbush-ai
MSG
