# Model And Data Plan

## Runtime Targets

- Text model: NVIDIA Nemotron 3 Nano 4B GGUF served through llama.cpp.
- Vision model: OpenBMB MiniCPM-V 4.6 GGUF through llama.cpp `llama-mtmd-cli`, with local image heuristics as fallback if model files are absent.
- Ask safety layer: model-first llama.cpp answers with deterministic risk banners, source selection,
  and compact guardrail anchors. If the text model is unavailable, Ask mode says so instead of
  inventing a deterministic prose answer.

## Current Pi Models

The service-managed Pi build targets `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF` with `NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf` for local text/RAG synthesis.

Photo triage targets `openbmb/MiniCPM-V-4.6-gguf`:

- `/home/vanveluwen/models/minicpm-v-4.6/MiniCPM-V-4_6-Q4_K_M.gguf`
- `/home/vanveluwen/models/minicpm-v-4.6/mmproj-model-f16.gguf`

The app invokes `llama-mtmd-cli` per photo request, then maps the VLM subject type into deterministic field-safety guidance.

## Fine-Tune Goal

Tune response style and structure, not factual truth from scratch.

The LoRA dataset should teach:

- concise Australian field-assistant tone
- source-aware answers
- uncertainty language
- explicit emergency escalation
- "do not eat wild mushrooms" guardrails
- no photo-only edible approvals

## Minimum Training Dataset Shape

JSONL records:

```json
{"instruction":"Can I eat this wild mushroom?","context":"NSW Health wild mushroom warning","response":"Do not eat wild mushrooms...","safety_tags":["mushroom","poisoning","no_edible_approval"]}
```

## Evaluation Set

Include regression prompts for:

- snake bite
- funnel-web or mouse spider bite
- unknown mushroom photo
- edible plant request
- severe bleeding
- heat illness
- lost walker
- cloud/weather forecast confusion

## Publish Artifacts

- Model repo: `outbush-ai-llama-cpp-lora`
- Dataset repo: `outbush-ai-field-safety-dataset`
- Space repo: `outbush-ai`

All model cards should state: not medical advice, not a species-certification tool, and not a replacement for emergency services.

## Current Vision Training Shape

`modal_jobs/outbush_species_finetune.py` now exports the field-tuned classifier from 95 target labels: 26 snakes, 10 spiders, 10 marine hazards, 20 plants, 10 bush-tucker labels, 10 mushrooms, 8 cloud/weather classes, and crocodile context. It resolves iNaturalist taxa by name for wildlife/plants/fungi and pulls cloud examples from Wikimedia Commons.

## Current Offline Knowledge Pack

- Builder: `scripts/build_knowledge_db.py`
- Artifact: `data/outbush_knowledge.sqlite`
- Format: SQLite with `sources`, `knowledge_items`, `meta`, and FTS5 table `knowledge_fts`
- Runtime: `outbush_ai.retrieval.KnowledgeIndex` prefers the packaged SQLite DB and falls back to in-memory content if the DB is missing or unreadable.
- App surface: `/api/encyclopedia` and the mobile Encyclopedia tab search the same offline pack used by chat/RAG.
- Size target: 325-650 items. Current generated pack: 348 items, including 50 national parks and NSW ranger-tip content.
