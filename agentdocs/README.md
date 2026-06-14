# Outbush AI Agent Guide

Outbush AI is a small offline-first Gradio/FastAPI field assistant for Australian bushwalking. The app is designed to run in three places:

- local development on a laptop
- Hugging Face Spaces for the hackathon demo
- a Raspberry Pi 5 acting as a local Wi-Fi appliance

The user-facing app is deliberately conservative. Emergency, poisoning, mushroom, snake, spider, weather, and wildlife guidance must remain useful when every model is unavailable.

## Start Here

- `app.py` wires the HTTP API and Gradio server.
- `outbush_ai/frontend.py` contains the whole browser UI as a static HTML string.
- `outbush_ai/core.py` is the main product logic and safety orchestration.
- `outbush_ai/content.py` is the offline source corpus for RAG and checklist/danger cards.
- `outbush_ai/retrieval.py` loads the packaged SQLite FTS5 knowledge database.
- `outbush_ai/vision.py` wraps the optional SmolVLM2 GGUF runtime through llama.cpp `llama-mtmd-cli`.
- `outbush_ai/species_model.py` wraps the lightweight field-tuned dangerous-species classifier.
- `scripts/build_knowledge_db.py` rebuilds `data/outbush_knowledge.sqlite` from `content.py`.

## Local Commands

```bash
. .venv/bin/activate
python scripts/build_knowledge_db.py
python -m unittest discover -s tests
python app.py
```

Open `http://127.0.0.1:7860`.

## Non-Negotiables

- Never tell a user a wild mushroom, plant, animal, or marine creature is safe to touch or eat from app output.
- Snake bites are treated as potentially life-threatening and route to Triple Zero (000).
- Funnel-web and mouse spider bites route to emergency pressure immobilisation guidance.
- Redback spider guidance is intentionally different from funnel-web guidance.
- Offline weather/climate guidance must not masquerade as a live forecast.
- The app must still pass tests with no model binaries present.
