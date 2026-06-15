# Verification

Use these checks before publishing.

## Unit And RAG

```bash
. .venv/bin/activate
python scripts/build_knowledge_db.py
python -m unittest discover -s tests
```

Expected outcomes:

- mushroom and foraging guardrails survive deterministic and llama-backed answers
- snake bite first aid includes Triple Zero and pressure immobilisation
- RAG uses packaged SQLite, not just in-memory fallback
- RAG item count is 325-650 and includes top-50 park, ranger-tip and bush-tucker coverage
- photo flow handles no image, uploaded image, species classifier, and MiniCPM-V-style results
- Modal training target tests cover the requested snake, spider, marine, plant, bush-tucker, mushroom and cloud categories

## Local HTTP Smoke

```bash
. .venv/bin/activate
OUTBUSH_PORT=7860 python app.py
python scripts/pi_smoke_test.py http://127.0.0.1:7860
```

## Hugging Face Space Smoke

```bash
python scripts/pi_smoke_test.py https://build-small-hackathon-outbush-ai.hf.space
curl -sS https://build-small-hackathon-outbush-ai.hf.space/api/health | python -m json.tool
```

`species_model_configured` should be true once the model JSON is present in the Space.

## Pi Smoke

```bash
ssh vanveluwen@vanveluwen-pi5 'cd ~/outbush-ai && . .venv/bin/activate && python scripts/pi_smoke_test.py http://127.0.0.1:7860'
python scripts/pi_smoke_test.py http://vanveluwen-pi5:7860
```

Check service state if the smoke test fails:

```bash
ssh vanveluwen@vanveluwen-pi5 'systemctl status outbush-ai --no-pager; ss -ltnp | grep -E "7860|8080"'
```
