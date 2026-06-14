# Model And Data Plan

## Runtime Targets

- Text model: small GGUF model served through llama.cpp, target Qwen2.5-3B-Instruct Q4_K_M or similar.
- Vision model: SmolVLM2-2.2B-Instruct-GGUF Q4_K_M through llama.cpp `llama-mtmd-cli`, with local image heuristics as fallback if model files are absent.
- Safety/RAG fallback: deterministic local code remains active even when a model is unavailable.

## Current Pi Smoke Model

The service-managed Pi build currently uses `Qwen/Qwen2.5-0.5B-Instruct-GGUF` with `qwen2.5-0.5b-instruct-q4_k_m.gguf`. This is a fast smoke model for proving llama.cpp runtime integration. The planned stronger field model remains a tuned small GGUF model, likely 1.5B-3B if Pi latency and memory stay within target.

Photo triage now has an offline VLM path using `ggml-org/SmolVLM2-2.2B-Instruct-GGUF`:

- `/home/vanveluwen/models/smolvlm2-2.2b/SmolVLM2-2.2B-Instruct-Q4_K_M.gguf`
- `/home/vanveluwen/models/smolvlm2-2.2b/mmproj-SmolVLM2-2.2B-Instruct-Q8_0.gguf`

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

## Current Offline Knowledge Pack

- Builder: `scripts/build_knowledge_db.py`
- Artifact: `data/outbush_knowledge.sqlite`
- Format: SQLite with `sources`, `knowledge_items`, `meta`, and FTS5 table `knowledge_fts`
- Runtime: `outbush_ai.retrieval.KnowledgeIndex` prefers the packaged SQLite DB and falls back to in-memory content if the DB is missing or unreadable.
- App surface: `/api/encyclopedia` and the mobile Encyclopedia tab search the same offline pack used by chat/RAG.
