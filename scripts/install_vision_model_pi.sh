#!/usr/bin/env bash
set -euo pipefail

MODEL_REPO="${MODEL_REPO:-ggml-org/SmolVLM2-2.2B-Instruct-GGUF}"
MODEL_DIR="${MODEL_DIR:-/home/vanveluwen/models/smolvlm2-2.2b}"
TEXT_MODEL_FILE="${TEXT_MODEL_FILE:-SmolVLM2-2.2B-Instruct-Q4_K_M.gguf}"
MMPROJ_FILE="${MMPROJ_FILE:-mmproj-SmolVLM2-2.2B-Instruct-Q8_0.gguf}"

mkdir -p "$MODEL_DIR"

download_file() {
  local file="$1"
  local url="https://huggingface.co/${MODEL_REPO}/resolve/main/${file}"
  if [[ -s "$MODEL_DIR/$file" ]]; then
    echo "Already present: $MODEL_DIR/$file"
    return
  fi
  echo "Downloading $file from $MODEL_REPO..."
  if command -v hf >/dev/null 2>&1; then
    hf download "$MODEL_REPO" "$file" --local-dir "$MODEL_DIR"
  else
    wget -c -O "$MODEL_DIR/$file" "$url"
  fi
}

download_file "$TEXT_MODEL_FILE"
download_file "$MMPROJ_FILE"

cat <<EOF
Vision model files are installed:
  $MODEL_DIR/$TEXT_MODEL_FILE
  $MODEL_DIR/$MMPROJ_FILE

Expected app environment:
  OUTBUSH_VISION_BACKEND=llama_cpp_mtmd
  OUTBUSH_VISION_MODEL=$MODEL_DIR/$TEXT_MODEL_FILE
  OUTBUSH_VISION_MMPROJ=$MODEL_DIR/$MMPROJ_FILE
EOF
