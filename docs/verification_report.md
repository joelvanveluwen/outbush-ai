# Outbush AI Verification Report

Generated: 2026-06-14

## 2026-06-14 Completion Update

- Hugging Face auth verified as `joelvanveluwen` with org `build-small-hackathon`.
- Modal auth verified under profile `joel-vanveluwen`.
- Modal secret `huggingface-token` created from the local HF auth token for remote model upload.
- `modal_jobs/outbush_species_finetune.py` ran successfully on Modal.
- The Modal job trained the Outbush dangerous-species classifier from 168 licensed iNaturalist examples across 14 labels:
  - yellow-bellied sea snake
  - red-bellied black snake
  - eastern brown snake
  - western brown snake
  - tiger snake
  - coastal taipan
  - inland taipan
  - Sydney funnel-web spider
  - redback spider
  - blue-ringed octopus
  - reef stonefish
  - box jellyfish
  - saltwater crocodile
  - gympie stinging tree
- Model repo published: `build-small-hackathon/outbush-dangerous-species-classifier`.
- Space repo published: `build-small-hackathon/outbush-ai`, commit `eb87a5ffab1b15a52026c65b47d79275ba5e092d`.
- Public Space smoke passed: `python scripts/pi_smoke_test.py https://build-small-hackathon-outbush-ai.hf.space`.
- Public Space health showed 65 SQLite RAG items and the tuned species model active with 14 labels.
- Browser verification on the public Space showed the new logo, favicon link, `#0c3709` / `#DDDE53` colour variables, tab navigation, `offline ready` status, and no console errors.
- Pi sync and DB rebuild completed at `~/outbush-ai`; service was restarted through systemd auto-restart.
- Pi health showed all model paths active:
  - Qwen2.5 GGUF text model through llama.cpp
  - SmolVLM2 GGUF through `llama-mtmd-cli`
  - Outbush field-tuned dangerous-species classifier from `models/outbush_dangerous_species_classifier.json`
- Pi LAN smoke passed: `python scripts/pi_smoke_test.py http://vanveluwen-pi5:7860`.
- Pi photo endpoint tested with `IMG_4103.jpg`; after conflict gating, the field-kit photo stayed `risk_level: normal` despite a low-margin classifier guess and a contradictory SmolVLM hallucination.
- Unit tests passed: `python -m unittest discover -s tests` ran 20 tests successfully.

## Completed Evidence

### Plan document

- `the_plan.html` exists as a standalone HTML document.
- It contains mobile viewport metadata, source links, feature cards, safety policy, implementation architecture, Pi plan, and completion goals.
- Local check confirmed the document contains the named feature sections and 16 external reference links.

### Local app

- Local venv installed `requirements.txt` successfully with Gradio 6.18.0.
- `python scripts/build_knowledge_db.py` generated `data/outbush_knowledge.sqlite` with 13 items.
- `python -m unittest discover -s tests` passed: 9 tests.
- `python -m py_compile outbush_ai/*.py tests/test_core.py scripts/pi_smoke_test.py modal_jobs/outbush_lora_smoke.py app.py` passed.
- App started locally on port 7861.
- `python scripts/pi_smoke_test.py http://127.0.0.1:7861` passed.
- `http://127.0.0.1:7861/gradio_api/info` exposed `chat`, `photo_identify`, `first_aid`, `checklist`, `encyclopedia`, `weather`, and `health`.
- Browser check loaded the custom UI, submitted "Can I eat this wild mushroom?", rendered the critical mushroom warning, and reported no console errors.
- Local smoke now also verifies `/api/encyclopedia` and the SQLite knowledge backend.

### Raspberry Pi

- Pi reachable at `vanveluwen-pi5` / `192.168.86.76`.
- Key-based SSH was installed for `vanveluwen`.
- Pi facts observed:
  - Hostname: `vanveluwen-pi5`
  - Kernel: Linux 6.18.29+rpt-rpi-2712 aarch64
  - Python: 3.13.5
  - Memory: 7.9 GiB total, about 6.6 GiB available during inspection
  - Root filesystem: 29 GB total, 17 GB available during inspection
  - NetworkManager active; `hostapd` inactive
- Repo synced to `~/outbush-ai`.
- Pi venv created and installed `requirements.txt`.
- Pi unit tests passed: 9 tests.
- Packaged SQLite knowledge DB present at `/home/vanveluwen/outbush-ai/data/outbush_knowledge.sqlite`.
- Pi app started on port 7862.
- Pi-local smoke test passed: `python scripts/pi_smoke_test.py http://127.0.0.1:7862`.
- LAN smoke test passed from Mac: `python scripts/pi_smoke_test.py http://vanveluwen-pi5:7862`.
- Browser loaded `http://vanveluwen-pi5:7862/`, showed title `Outbush AI`, status `offline ready`, Ask and Photo UI, and no console errors.
- Pi fallback process memory observed around 143 MB RSS, with about 6.6 GB system memory available.
- Endpoint timings over LAN in fallback mode:
  - chat: about 0.135 s
  - first aid: about 0.025 s
  - weather: about 0.023 s
  - checklist: about 0.136 s

### Pi systemd appliance mode

- `outbush-ai.service` installed, enabled, and started.
- `llama-server.service` installed, enabled, and started.
- Service-managed app listens on `0.0.0.0:7860`.
- Service-managed llama.cpp listens on `127.0.0.1:8080`.
- Pi-local service smoke test passed: `python scripts/pi_smoke_test.py http://127.0.0.1:7860`.
- LAN service smoke test passed: `python scripts/pi_smoke_test.py http://vanveluwen-pi5:7860`.
- Browser loaded `http://vanveluwen-pi5:7860/`, title `Outbush AI`, status `offline ready`, no console errors.
- Browser Encyclopedia tab search rendered `Wild mushroom rule` and the NSW Health source with no console errors.

### llama.cpp runtime

- Source build attempt reached core library compilation but `llama-server` failed because embedded UI asset provisioning generated zero-size C++ arrays after upstream HF bucket downloads failed.
- Recovered with official prebuilt release asset `llama-b9616-bin-ubuntu-arm64.tar.gz`.
- Verified binary:
  - `llama-server --version`: version 9616, built for Linux aarch64
  - `llama-cli --version`: version 9616, built for Linux aarch64
- Downloaded public smoke model:
  - Repo: `Qwen/Qwen2.5-0.5B-Instruct-GGUF`
  - File: `qwen2.5-0.5b-instruct-q4_k_m.gguf`
  - Local path: `/home/vanveluwen/models/qwen2.5-0.5b-instruct-q4_k_m.gguf`
- Direct llama.cpp completion on Pi returned in about 2.9 seconds for a short prompt.
- Outbush app with `OUTBUSH_USE_LLAMA=1` used `model_backend: llama.cpp`.
- LAN chat request through service-managed Outbush + llama.cpp returned in about 13.0 seconds for a bushwalk preparation prompt.
- LAN mushroom safety request through service-managed Outbush + llama.cpp returned in about 5.8 seconds, risk `critical`, with deterministic "do not eat wild mushrooms" and "foraging limit" guardrails.
- Memory after both services were running:
  - `llama-server`: about 663 MB RSS
  - Outbush app: about 144 MB RSS
  - System available memory: about 6.3 GB

### Wi-Fi hotspot profile

- NetworkManager hotspot profile `Outbush-AI` created on `wlan0`.
- Verified settings:
  - `802-11-wireless.mode`: `ap`
  - `ipv4.method`: `shared`
  - `ipv4.addresses`: `10.42.0.1/24`
  - `connection.autoconnect`: `no`
- The profile was not activated remotely because doing so would move `wlan0` off the current LAN and can disconnect SSH before a phone/console test is possible.

### Safety checks

- Mushroom chat returns critical risk and "Do not eat wild mushrooms."
- Mushroom photo fallback returns critical risk and source `NSW Health - Wild mushroom poisoning`.
- Snake bite first-aid flow includes Triple Zero and pressure immobilisation.
- Danger cards include source URLs.
- Weather/cloud answers distinguish observation from live forecast.
- Checklist includes PLB, live BoM forecast, park alerts, and copy/export-ready `[ ]` text.
- Encyclopedia search uses SQLite FTS and returns source-labelled offline results.

### Operational notes

- After syncing the Encyclopedia route to the Pi, the first service process still returned 404 for `/api/encyclopedia`; a clean `sudo systemctl restart outbush-ai` loaded the updated route table and OpenAPI then included `/api/encyclopedia`.

## Added Implementation Scaffolding

- `README.md` now includes Hugging Face Space metadata.
- Project-local HF CLI skill installed at `.agents/skills/hf-cli`.
- `scripts/hf_publish_space.sh` publishes the Space after HF auth is configured.
- `requirements-dev.txt` installs Modal for training jobs.
- `modal_jobs/outbush_lora_smoke.py` validates Modal remote execution before real LoRA training.
- `scripts/modal_smoke.sh` runs the Modal smoke job.
- `systemd/outbush-ai.service` and `systemd/llama-server.service` provide Pi service templates.
- `scripts/install_pi_services.sh` installs/enables the Outbush service on the Pi.
- `scripts/install_llama_cpp_pi.sh` installs the official llama.cpp ARM64 prebuilt and Qwen smoke GGUF on the Pi.
- `scripts/configure_hotspot_nmcli.sh` creates the `Outbush-AI` NetworkManager hotspot connection without activating it.
- `docs/model_and_data_plan.md`, `docs/submission_checklist.md`, and `docs/field_notes_template.md` document the remaining model/submission/field-proof work.
- `data/outbush_knowledge.sqlite` provides the current repeatable offline knowledge artifact.

## Remaining Manual Field Proof

These items require physical access or a real field session and were not attempted from this remote environment:

- Hotspot activation: `Outbush-AI` profile exists, but activating `wlan0` over SSH can disconnect the Pi. Activate with console access or a rollback timer.
- Phone-in-airplane-mode proof against `http://outbush.local`.
- Real field notes/demo video/social post using `docs/field_notes_template.md`.
