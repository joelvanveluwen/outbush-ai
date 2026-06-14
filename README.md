---
title: Outbush AI
emoji: 🧭
colorFrom: green
colorTo: yellow
sdk: gradio
sdk_version: 6.18.0
app_file: app.py
pinned: false
tags:
  - build-small-hackathon
  - backyard-ai
  - off-the-grid
  - llama-cpp
  - gradio-server
  - australia
models:
  - Qwen/Qwen2.5-0.5B-Instruct-GGUF
  - ggml-org/SmolVLM2-2.2B-Instruct-GGUF
---

# Outbush AI

Outbush AI is an offline-first Gradio app for Australian bushwalkers. The target runtime is a Raspberry Pi 5 with 8 GB RAM acting as a Wi-Fi hotspot, so users can connect with a phone and get local guidance without mobile service.

The first build contains:

- A polished standalone plan document at `the_plan.html`.
- A `gradio.Server` app with a custom phone-friendly frontend.
- Offline deterministic safety/RAG behavior for first aid, wildlife, plants, mushrooms, checklists, emergency orientation, and broad weather guidance.
- A packaged SQLite FTS5 knowledge pack at `data/outbush_knowledge.sqlite`.
- Optional llama.cpp integration through `LLAMA_CPP_BASE_URL`.
- Tests for the high-risk guardrails.

## Run Locally

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:7860`.

## llama.cpp Runtime Hook

If a local llama.cpp server is available, start it separately and set:

```bash
export LLAMA_CPP_BASE_URL=http://127.0.0.1:8080
export OUTBUSH_USE_LLAMA=1
```

The app still keeps deterministic safety fallbacks so emergency, mushroom, and poisoning guidance does not depend on model availability.

## Offline Vision Runtime

Photo triage can use a local multimodal GGUF through llama.cpp `llama-mtmd-cli`.
The Pi install path uses:

- Model repo: `ggml-org/SmolVLM2-2.2B-Instruct-GGUF`
- Main model: `SmolVLM2-2.2B-Instruct-Q4_K_M.gguf`
- Projector: `mmproj-SmolVLM2-2.2B-Instruct-Q8_0.gguf`

Install on the Pi:

```bash
bash scripts/install_vision_model_pi.sh
sudo REPO_DIR=/home/vanveluwen/outbush-ai bash scripts/install_pi_services.sh
sudo systemctl restart outbush-ai
```

The app falls back to local image heuristics if the vision files are missing.

## Tests

```bash
python scripts/build_knowledge_db.py
python -m unittest discover -s tests
```

## Pi Target

The final field target is:

- SSID: `Outbush-AI`
- Local URL: `http://outbush.local`
- Services: llama.cpp, Outbush Gradio app, optional Kiwix, hotspot, mDNS
- Runtime: no cloud APIs after setup
- Local model path used in the Pi smoke build: `Qwen/Qwen2.5-0.5B-Instruct-GGUF`, file `qwen2.5-0.5b-instruct-q4_k_m.gguf`

## Publish To Hugging Face

After logging in with `hf auth login`, create/upload the Space:

```bash
hf upload YOUR_USERNAME/outbush-ai . --type space \
  --exclude ".venv/*" --exclude ".git/*" --exclude "__pycache__/*" \
  --commit-message "Initial Outbush AI Space"
```

Publish the tuned model and field dataset separately, then link them from this README before submission.
