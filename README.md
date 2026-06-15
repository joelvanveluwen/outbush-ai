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
  - track:backyard
  - off-the-grid
  - achievement:offgrid
  - llama-cpp
  - gradio-server
  - off-brand
  - achievement:offbrand
  - tiny-titan
  - modal
  - sponsor:modal
  - minicpm
  - sponsor:openbmb
  - nemotron
  - sponsor:nvidia
  - codex
  - australia
models:
  - nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF
  - openbmb/MiniCPM-V-4.6-gguf
  - build-small-hackathon/outbush-dangerous-species-classifier
---

![Outbush AI field kit](docs/outbush-readme-hero.png)

# Outbush AI

**out bush**

*/ˌaʊt ˈbʊʃ/*

In Australia, "out bush" means heading into remote wilderness, countryside, or bushland. It carries the spirit of leaving civilisation, living rough, or simply spending time reconnecting with nature and the land.

## The Idea

Australia is massive. Mobile phone services reach most people where they live, but many regional and remote areas still have no or poor data reception. That matters when you are bushwalking, camping, driving tracks, or walking beaches beyond reliable coverage.

Disconnecting and enjoying nature is fantastic until it isn't. The meme says "everything in Australia is trying to kill you"; that is overstated, but understanding risks from snakes, spiders, marine stingers, stinging trees, crocodile country, heat, storms, and even platypus spurs is central to being safe out bush.

My Mum works for the National Parks service, so when I came across a snake, odd insect, strange plant, or unfamiliar bird, I would take a photo and send it to her for identification after the hike.

## The Solution

Small open-source AI models change this process. I can bring a low-powered device like a Raspberry Pi with local language, image, and retrieval models that contain relevant Australian field information and important survival knowledge. A phone connects to the Pi's local Wi-Fi and asks questions or checks images without an internet connection.

When activated, the Raspberry Pi hosts Outbush AI locally. Ask mode prefers local llama.cpp text answers from NVIDIA Nemotron 3 Nano 4B, while safety footers, photo guardrails, first-aid flows, OpenBMB MiniCPM-V photo triage, and the field-tuned dangerous-species classifier keep field use conservative.

This hack is built for Australian wilderness context, but the pattern can be adapted for any region, climate, and risk profile.

## The Application

We were walking our dog on a quiet beach with no mobile reception and spotted something slithering along the sand. It was a snake I had never seen before. When I took a photo and processed it with Outbush AI, the app identified it as a yellow-bellied sea snake candidate and noted it as highly venomous. We stayed clear, continued our walk, and reported the animal to a wildlife rescue organisation.

Live hackathon Space: https://huggingface.co/spaces/build-small-hackathon/outbush-ai

## What It Does

- Phone-friendly Gradio/FastAPI app for offline Australian field support.
- SQLite FTS5 RAG pack with 358 local knowledge chunks for first aid, dangerous animals, plants, weather, top national parks, ranger tips, hiking, rainforest, coast, heat, and survival advice.
- Model-first Ask answers with source-ranked RAG context, plus guardrails for snake bite, funnel-web and redback spider bites, marine stingers, mushrooms, poisoning, heat, exposure, weather, and emergency orientation.
- NVIDIA Nemotron 3 Nano 4B GGUF text model via `LLAMA_CPP_BASE_URL`, with Space auto-setup when running on Hugging Face.
- Optional OpenBMB MiniCPM-V 4.6 GGUF photo triage through `llama-mtmd-cli`.
- Field-tuned dangerous-species image classifier trained from licensed iNaturalist examples and packaged for Hugging Face Space and Raspberry Pi use.
- Custom phone-first UI with local-processing glimmer states and random encyclopedia discovery.

## Run Locally

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build_knowledge_db.py
python app.py
```

Open `http://127.0.0.1:7860`.

## Nemotron llama.cpp Runtime Hook

If a local llama.cpp server is available, start it separately and set:

```bash
export LLAMA_CPP_BASE_URL=http://127.0.0.1:8080
export OUTBUSH_USE_LLAMA=1
```

Ask mode does not fabricate a deterministic prose answer when the text model is unavailable; it tells you to start or sync the local llama.cpp text model. First-aid, checklist, photo, weather, and encyclopedia routes still expose structured offline guidance.

On Hugging Face Spaces, `OUTBUSH_AUTO_SETUP_TEXT` defaults on when `SPACE_ID`/`HF_SPACE_ID` exists. The app downloads the llama.cpp x64 runtime and `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF` into `/tmp/outbush-ai-models`, starts `llama-server` on `127.0.0.1:8080`, and reports progress in `/api/health` under `text_model`.

## Offline Vision Runtime

Photo triage can use a local OpenBMB MiniCPM-V multimodal GGUF through llama.cpp `llama-mtmd-cli`.

- Model repo: `openbmb/MiniCPM-V-4.6-gguf`
- Pi-friendly main model: `MiniCPM-V-4_6-Q4_K_M.gguf`
- Projector: `mmproj-model-f16.gguf`

Install on the Pi:

```bash
bash scripts/install_vision_model_pi.sh
sudo REPO_DIR=/home/vanveluwen/outbush-ai bash scripts/install_pi_services.sh
sudo systemctl restart outbush-ai
```

## Field-Tuned Dangerous-Species Classifier

The Modal training job collects licensed image examples for 26 Australian snake labels, 10 spider labels, 10 marine hazards, 20 plants, 10 bush-tucker labels, 10 mushrooms, cloud/storm classes, plus crocodile context. It uses iNaturalist for wildlife, plants and fungi and Wikimedia Commons for cloud imagery, then exports a compact field-tuned classifier used alongside MiniCPM-V.

```bash
. .venv/bin/activate
modal run modal_jobs/outbush_species_finetune.py
hf download build-small-hackathon/outbush-dangerous-species-classifier \
  outbush_dangerous_species_classifier.json \
  --type model \
  --local-dir models
```

The packaged JSON classifier runs with Pillow only, so it works in the Space and on the Pi without heavy Python ML dependencies.

## Tests

```bash
python scripts/build_knowledge_db.py
python -m unittest discover -s tests
python scripts/pi_smoke_test.py http://127.0.0.1:7860
```

## Pi Target

- SSID: `Outbush-AI`
- Local URL: `http://outbush.local`
- Services: llama.cpp, Outbush Gradio app, hotspot, mDNS
- Runtime: no cloud APIs after setup
- Text model path used in the Pi build: `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`, file `NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf`
- Vision model path used in the Pi build: `openbmb/MiniCPM-V-4.6-gguf`, file `MiniCPM-V-4_6-Q4_K_M.gguf` with `mmproj-model-f16.gguf`

## Badge Signals

The Space YAML is tagged for Backyard AI, off-grid, custom UI/off-brand, Tiny Titan, Modal, OpenBMB MiniCPM, NVIDIA Nemotron, Codex, llama.cpp, and Australian field safety. The default local model choices stay in the small-model spirit for the Pi: Nemotron 3 Nano 4B for text and MiniCPM-V 4.6 for vision.

## Publish To Hugging Face

After logging in with `hf auth login`, publish the Space mirror:

```bash
bash scripts/hf_publish_space.sh
```
