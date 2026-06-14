# Architecture

Outbush AI is intentionally compact.

```mermaid
flowchart TD
  Browser["Phone browser / HF Space browser"] --> App["app.py Gradio Server + FastAPI routes"]
  App --> Core["outbush_ai/core.py"]
  Core --> RAG["retrieval.py SQLite FTS5"]
  RAG --> DB["data/outbush_knowledge.sqlite"]
  Core --> Content["content.py source corpus, checklist, danger cards"]
  Core --> Llama["optional llama.cpp text model"]
  Core --> Vision["optional SmolVLM2 llama-mtmd-cli"]
  Core --> Species["optional field-tuned species classifier JSON"]
  Core --> Weather["weather.py cached/live weather pack"]
```

## Request Flow

- `/api/chat` searches the local knowledge pack, applies risk banners, and optionally asks llama.cpp to synthesize the answer.
- `/api/photo` performs local pixel analysis, optional field-tuned species classification, optional SmolVLM2 classification, then applies conservative care notes.
- `/api/firstaid` searches the local RAG pack for a topic and returns first aid steps plus do-not guidance.
- `/api/encyclopedia` exposes direct local RAG search.
- `/api/weather` separates broad climate/profile guidance from cached or live weather pack data.
- `/api/health` reports whether SQLite, llama.cpp, SmolVLM2, and the species classifier are active.

## Data Flow

`outbush_ai/content.py` is the source of truth for RAG items. Run `python scripts/build_knowledge_db.py` after editing it. Tests expect the packaged SQLite database to be present and FTS-enabled.

The dangerous-species image classifier is trained by `modal_jobs/outbush_species_finetune.py`. It uploads artifacts to Hugging Face and the app can run from the checked-in JSON model at `models/outbush_dangerous_species_classifier.json`.

## Runtime Philosophy

The model paths are additive. The deterministic fallback is the safety floor; llama.cpp, SmolVLM2, and the field-tuned classifier improve specificity but do not replace guardrails.
