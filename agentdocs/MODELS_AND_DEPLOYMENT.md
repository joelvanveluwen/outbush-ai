# Models And Deployment

Outbush AI supports three model paths.

## Text Model

The Pi target runs Qwen2.5 0.5B Instruct GGUF through `llama-server` on `127.0.0.1:8080`. The app uses it only when both variables are set:

```bash
export LLAMA_CPP_BASE_URL=http://127.0.0.1:8080
export OUTBUSH_USE_LLAMA=1
```

## Vision-Language Model

SmolVLM2 GGUF is called through llama.cpp `llama-mtmd-cli` when these files exist:

- `OUTBUSH_VISION_CLI`
- `OUTBUSH_VISION_MODEL`
- `OUTBUSH_VISION_MMPROJ`

Install or refresh it on the Pi with:

```bash
bash scripts/install_vision_model_pi.sh
sudo REPO_DIR=/home/vanveluwen/outbush-ai bash scripts/install_pi_services.sh
sudo systemctl restart outbush-ai
```

## Field-Tuned Species Classifier

`modal_jobs/outbush_species_finetune.py` collects licensed iNaturalist photo examples for dangerous Australian species, trains a compact classifier artifact, and uploads it to Hugging Face.

Default model repo:

```bash
build-small-hackathon/outbush-dangerous-species-classifier
```

Run:

```bash
. .venv/bin/activate
modal run modal_jobs/outbush_species_finetune.py
```

Then download the model JSON into `models/`:

```bash
hf download build-small-hackathon/outbush-dangerous-species-classifier \
  outbush_dangerous_species_classifier.json \
  --type model \
  --local-dir models
```

The app can use this model with no extra runtime dependency beyond Pillow.

## Hugging Face Space

Publish the app mirror with:

```bash
bash scripts/hf_publish_space.sh
```

Check it with:

```bash
python scripts/pi_smoke_test.py https://build-small-hackathon-outbush-ai.hf.space
```

## Raspberry Pi

The known Pi host is `vanveluwen-pi5`. The service listens on `0.0.0.0:7860`.

```bash
rsync -az --delete --exclude .git --exclude .venv ./ vanveluwen@vanveluwen-pi5:~/outbush-ai/
ssh vanveluwen@vanveluwen-pi5 'sudo systemctl restart outbush-ai'
python scripts/pi_smoke_test.py http://vanveluwen-pi5:7860
```
