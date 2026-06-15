# RAG And Safety Notes

The offline knowledge pack is built from short, source-attributed notes in `outbush_ai/content.py` and generated structured notes in `outbush_ai/expanded_content.py`. Each `KnowledgeItem` has a source, tags, and a risk level.

The current pack is intentionally larger than the original hand-written corpus: 358 items, including 150 chunks for 50 national parks, 35 NSW ranger-tip notes, expanded wildlife/plant/marine/cloud coverage, bush tucker context, mushroom cautions, and survival-specific notes for lost, flood, lightning, alpine, coastal, and rainforest scenarios.

## How To Add Knowledge

1. Add or reuse a `Source` in `SOURCES`.
2. Add a concise `KnowledgeItem` with practical field guidance.
3. Include likely user phrasing in `tags`, including common misspellings or non-technical wording.
4. Run `python3 scripts/build_knowledge_db.py`.
5. Add or update tests for high-risk behavior.

For broad coverage additions, prefer extending the structured lists in `expanded_content.py` so the generated keys stay consistent and the main content file remains readable.

## Good RAG Items

- Short enough to fit into a small local prompt.
- Written as field action, not encyclopedic trivia.
- Explicit about uncertainty and escalation.
- Source-specific where first aid differs by hazard.

## Risk Routing

Critical topics should usually include one of:

- call Triple Zero (000)
- pressure immobilisation for Australian snake bite or funnel-web/mouse spider bite
- call Poisons Information Centre on 13 11 26 for poisoning or ingestion
- do not eat wild mushrooms
- avoid water edges in crocodile country

High-risk topics cover heat illness, cold exposure, storms, floods, stinging trees, redback bites, ticks/leeches, and remote navigation.

## Source Bias

Prefer Australian medical, parks, museum, and government sources:

- Healthdirect and state poisons services for first aid
- Australian Museum for species descriptions
- NSW/QLD/NT/Parks Australia for walking conditions
- Bureau of Meteorology for weather and thunderstorm concepts

Do not paste long source text into the repo. Paraphrase into short local guidance and keep the URL.
