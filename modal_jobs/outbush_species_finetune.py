"""Modal training job for the Outbush dangerous-species image classifier."""

from __future__ import annotations

import json
import math
import os
import tempfile
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import modal


DEFAULT_REPO_ID = "build-small-hackathon/outbush-dangerous-species-classifier"
MODEL_FILE = "outbush_dangerous_species_classifier.json"
MANIFEST_FILE = "vision_training_manifest.json"

TAXA = (
    {
        "label": "yellow-bellied sea snake",
        "taxon_id": 35164,
        "subject_type": "snake",
        "risk": "critical",
        "hazard_group": "snake",
        "source": {
            "title": "Australian Museum - Yellow-bellied Sea Snake",
            "url": "https://australian.museum/learn/animals/reptiles/yellow-bellied-sea-snake/",
        },
        "field_guidance": "Keep people and dogs back from the animal. Treat any suspected bite as a snake-bite emergency and call 000.",
    },
    {
        "label": "red-bellied black snake",
        "taxon_id": 35153,
        "subject_type": "snake",
        "risk": "critical",
        "hazard_group": "snake",
        "source": {
            "title": "Australian Museum - Red-bellied Black Snake",
            "url": "https://australian.museum/learn/animals/reptiles/red-bellied-black-snake/",
        },
        "field_guidance": "Do not approach for a closer look. Give the snake space and use snake-bite first aid for any suspected bite.",
    },
    {
        "label": "eastern brown snake",
        "taxon_id": 35140,
        "subject_type": "snake",
        "risk": "critical",
        "hazard_group": "snake",
        "source": {
            "title": "Australian Museum - Eastern Brown Snake",
            "url": "https://australian.museum/learn/animals/reptiles/eastern-brown-snake/",
        },
        "field_guidance": "Back away slowly, leave an escape path, and treat any suspected bite as life-threatening.",
    },
    {
        "label": "western brown snake",
        "taxon_id": 111069,
        "subject_type": "snake",
        "risk": "critical",
        "hazard_group": "snake",
        "source": {
            "title": "Australian Museum - Western Brown Snakes",
            "url": "https://australian.museum/learn/animals/reptiles/western-brown-snakes/",
        },
        "field_guidance": "Do not handle or try to identify at close range. Use snake-bite first aid for any suspected bite.",
    },
    {
        "label": "tiger snake",
        "taxon_id": 35178,
        "subject_type": "snake",
        "risk": "critical",
        "hazard_group": "snake",
        "source": {
            "title": "Australian Museum - Tiger Snake",
            "url": "https://australian.museum/learn/animals/reptiles/tiger-snake/",
        },
        "field_guidance": "Keep distance, especially near wetlands or damp habitat. Use snake-bite first aid for any suspected bite.",
    },
    {
        "label": "coastal taipan",
        "taxon_id": 35170,
        "subject_type": "snake",
        "risk": "critical",
        "hazard_group": "snake",
        "source": {
            "title": "Australian Museum - Coastal Taipan",
            "url": "https://australian.museum/learn/animals/reptiles/coastal-taipan/",
        },
        "field_guidance": "Stay well clear and do not try to distinguish taipans from other brown-coloured elapids in the field.",
    },
    {
        "label": "inland taipan",
        "taxon_id": 35172,
        "subject_type": "snake",
        "risk": "critical",
        "hazard_group": "snake",
        "source": {
            "title": "Australian Museum - Inland Taipan",
            "url": "https://australian.museum/learn/animals/reptiles/inland-taipan/",
        },
        "field_guidance": "Treat any suspected taipan encounter with distance-first caution and any bite as a snake-bite emergency.",
    },
    {
        "label": "sydney funnel-web spider",
        "taxon_id": 205276,
        "subject_type": "spider",
        "risk": "critical",
        "hazard_group": "spider",
        "source": {
            "title": "Australian Museum - Sydney Funnel-web Spider",
            "url": "https://australian.museum/learn/animals/spiders/sydney-funnel-web-spider/",
        },
        "field_guidance": "Do not handle. For suspected funnel-web or mouse spider bite, call 000 and use pressure immobilisation.",
    },
    {
        "label": "redback spider",
        "taxon_id": 146765,
        "subject_type": "spider",
        "risk": "high",
        "hazard_group": "spider",
        "source": {
            "title": "Australian Museum - Redback Spider",
            "url": "https://australian.museum/learn/animals/spiders/redback-spider/",
        },
        "field_guidance": "Shake out gear and use gloves around stored items. For bites, use a cold pack and seek advice for severe pain.",
    },
    {
        "label": "blue-ringed octopus",
        "taxon_id": 199918,
        "subject_type": "marine",
        "risk": "critical",
        "hazard_group": "marine",
        "source": {
            "title": "Australian Museum - Blue-lined Octopus",
            "url": "https://australian.museum/learn/animals/molluscs/blue-lined-octopus/",
        },
        "field_guidance": "Never handle rock-pool octopus, shells, or hidden marine animals. Call 000 for suspected bite or breathing symptoms.",
    },
    {
        "label": "reef stonefish",
        "taxon_id": 64490,
        "subject_type": "marine",
        "risk": "critical",
        "hazard_group": "marine",
        "source": {
            "title": "Australian Museum - Reef Stonefish",
            "url": "https://australian.museum/learn/animals/fishes/reef-stonefish-synanceia-verrucosa-bloch-schneider-1801/",
        },
        "field_guidance": "Wear protective footwear in reef or northern coastal habitat. Call 000 for severe pain or systemic symptoms.",
    },
    {
        "label": "box jellyfish",
        "taxon_id": 321669,
        "subject_type": "marine",
        "risk": "critical",
        "hazard_group": "marine",
        "source": {
            "title": "Australian Museum - Box Jellyfish",
            "url": "https://australian.museum/learn/animals/jellyfish/boxjellyfish/",
        },
        "field_guidance": "Follow local stinger signs and call 000 for major tropical jellyfish stings.",
    },
    {
        "label": "saltwater crocodile",
        "taxon_id": 26068,
        "subject_type": "animal",
        "risk": "critical",
        "hazard_group": "crocodile",
        "source": {
            "title": "Australian Museum - Estuarine Crocodile",
            "url": "https://australian.museum/learn/animals/reptiles/estuarine-crocodile/",
        },
        "field_guidance": "Obey crocodile signs and keep well back from northern water edges.",
    },
    {
        "label": "gympie stinging tree",
        "taxon_id": 129503,
        "subject_type": "plant",
        "risk": "high",
        "hazard_group": "plant",
        "source": {
            "title": "Queensland Parks - Lamington visiting safely",
            "url": "https://parks.qld.gov.au/parks/lamington/visiting-safely",
        },
        "field_guidance": "Do not touch stinging tree leaves, stems, or dead leaves. Seek care for severe pain.",
    },
)

app = modal.App("outbush-ai-species-finetune")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "huggingface_hub>=1.1.0",
    "pillow>=10.4",
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("huggingface-token")],
    timeout=3600,
)
def train_and_upload(repo_id: str = DEFAULT_REPO_ID, images_per_label: int = 16) -> dict[str, Any]:
    from huggingface_hub import HfApi

    trained_at = datetime.now(timezone.utc).isoformat()
    classes: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for taxon in TAXA:
        observations = _fetch_observations(int(taxon["taxon_id"]), per_page=max(images_per_label * 3, 30))
        features: list[list[float]] = []
        for observation in observations:
            if len(features) >= images_per_label:
                break
            photo = _first_photo(observation)
            if not photo:
                continue
            try:
                image_bytes = _download_image(photo["url"])
                vector = extract_image_features(image_bytes)
            except Exception as exc:
                failures.append({"label": str(taxon["label"]), "error": str(exc)})
                continue
            features.append(vector)
            manifest.append(
                {
                    "label": taxon["label"],
                    "taxon_id": taxon["taxon_id"],
                    "observation_id": observation.get("id"),
                    "observed_on": observation.get("observed_on"),
                    "photo_url": photo["url"],
                    "photo_license": photo.get("license_code") or observation.get("license_code") or "",
                    "attribution": photo.get("attribution") or "",
                    "uri": observation.get("uri") or "",
                }
            )
            time.sleep(0.05)
        if not features:
            failures.append({"label": str(taxon["label"]), "error": "no usable licensed examples"})
            continue
        centroid = [round(sum(values) / len(values), 6) for values in zip(*features)]
        classes.append(
            {
                "label": taxon["label"],
                "taxon_id": taxon["taxon_id"],
                "subject_type": taxon["subject_type"],
                "risk": taxon["risk"],
                "hazard_group": taxon["hazard_group"],
                "source": taxon["source"],
                "field_guidance": taxon["field_guidance"],
                "n_examples": len(features),
                "centroid": centroid,
            }
        )

    model = {
        "model_type": "outbush-centroid-image-classifier",
        "version": "2026-06-14",
        "repo_id": repo_id,
        "trained_at": trained_at,
        "training_source": "licensed iNaturalist API observations",
        "training_examples": len(manifest),
        "confidence_threshold_medium": 0.88,
        "confidence_threshold_high": 0.94,
        "confidence_margin_medium": 0.015,
        "confidence_margin_high": 0.035,
        "classes": classes,
        "limits": [
            "This classifier is a field triage signal, not species certification.",
            "Low-confidence predictions must not override deterministic safety guidance.",
            "Do not touch, handle, or eat wild animals, plants, or fungi based on this output.",
        ],
    }

    readme = _model_card(repo_id, model, manifest, failures)
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / MODEL_FILE).write_text(json.dumps(model, indent=2), encoding="utf-8")
        (folder / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (folder / "training_report.json").write_text(
            json.dumps({"model": model, "failures": failures}, indent=2),
            encoding="utf-8",
        )
        (folder / "README.md").write_text(readme, encoding="utf-8")
        api = HfApi(token=os.environ["HF_TOKEN"])
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
        api.upload_folder(
            repo_id=repo_id,
            repo_type="model",
            folder_path=str(folder),
            commit_message="Train Outbush dangerous species classifier",
        )

    return {
        "repo_id": repo_id,
        "classes": len(classes),
        "training_examples": len(manifest),
        "failures": failures[:8],
        "model_file": MODEL_FILE,
    }


def _fetch_observations(taxon_id: int, per_page: int) -> list[dict[str, Any]]:
    params = {
        "taxon_id": taxon_id,
        "photos": "true",
        "licensed": "true",
        "quality_grade": "research",
        "order_by": "votes",
        "order": "desc",
        "per_page": min(per_page, 200),
    }
    url = "https://api.inaturalist.org/v1/observations?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "outbush-ai/1.0"})
    with urlopen(request, timeout=45) as response:
        data = json.loads(response.read().decode("utf-8"))
    return list(data.get("results", []))


def _first_photo(observation: dict[str, Any]) -> dict[str, Any] | None:
    photos = observation.get("photos") or []
    for photo in photos:
        url = str(photo.get("url") or "")
        if not url:
            continue
        return {
            "url": url.replace("square.", "medium."),
            "license_code": photo.get("license_code"),
            "attribution": photo.get("attribution"),
        }
    return None


def _download_image(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "outbush-ai/1.0"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def extract_image_features(image_bytes: bytes) -> list[float]:
    from PIL import Image

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size
            rgb = image.convert("RGB")
            rgb.thumbnail((96, 96))
            pixel_data = rgb.get_flattened_data() if hasattr(rgb, "get_flattened_data") else rgb.getdata()
            pixels = list(pixel_data)
    except Exception as exc:
        raise ValueError(f"image could not be decoded: {exc}") from exc
    if not pixels:
        raise ValueError("image has no pixels")

    n = float(len(pixels))
    channels = list(zip(*pixels))
    means = [sum(channel) / (255.0 * n) for channel in channels]
    stds = []
    for idx, channel in enumerate(channels):
        mean_255 = means[idx] * 255.0
        variance = sum((value - mean_255) ** 2 for value in channel) / n
        stds.append(math.sqrt(variance) / 255.0)

    brightness_values = [(r + g + b) / (3.0 * 255.0) for r, g, b in pixels]
    brightness_mean = sum(brightness_values) / n
    brightness_std = math.sqrt(sum((value - brightness_mean) ** 2 for value in brightness_values) / n)

    features: list[float] = []
    features.extend(means)
    features.extend(stds)
    features.extend([brightness_mean, brightness_std])
    features.extend(_histogram(brightness_values, 8))
    for channel in channels:
        features.extend(_histogram([value / 255.0 for value in channel], 4))
    features.append(min(width / max(height, 1), 3.0) / 3.0)
    features.append(min(height / max(width, 1), 3.0) / 3.0)
    features.extend(_grid_brightness_features(pixels, rgb.size[0], rgb.size[1]))
    return [round(value, 6) for value in features]


def _histogram(values: list[float], bins: int) -> list[float]:
    counts = [0] * bins
    for value in values:
        index = min(bins - 1, max(0, int(value * bins)))
        counts[index] += 1
    total = float(len(values) or 1)
    return [count / total for count in counts]


def _grid_brightness_features(pixels: list[tuple[int, int, int]], width: int, height: int) -> list[float]:
    sums = [0.0] * 9
    counts = [0] * 9
    for index, (red, green, blue) in enumerate(pixels):
        x = index % width
        y = index // width
        gx = min(2, int((x / max(width, 1)) * 3))
        gy = min(2, int((y / max(height, 1)) * 3))
        bucket = gy * 3 + gx
        sums[bucket] += (red + green + blue) / (3.0 * 255.0)
        counts[bucket] += 1
    return [sums[index] / counts[index] if counts[index] else 0.0 for index in range(9)]


def _model_card(repo_id: str, model: dict[str, Any], manifest: list[dict[str, Any]], failures: list[dict[str, str]]) -> str:
    labels = "\n".join(
        f"- {item['label']}: {item['n_examples']} examples, risk={item['risk']}"
        for item in model["classes"]
    )
    return f"""---
license: mit
tags:
  - image-classification
  - australia
  - bushwalking
  - safety
  - modal
---

# Outbush Dangerous Species Classifier

This is the compact field-tuned image classifier used by Outbush AI for offline dangerous-species triage.

It was trained from licensed iNaturalist observation photos and exported as `{MODEL_FILE}` so the Hugging Face Space and Raspberry Pi can run it with Pillow only.

Repository: `{repo_id}`

Training examples: {len(manifest)}

Labels:

{labels}

Limits:

- This is not species certification.
- Use predictions as candidate hints only.
- Do not touch, handle, or eat wild animals, plants, marine creatures, or fungi based on model output.
- For bites, stings, poisoning, collapse, breathing trouble, or severe symptoms, use emergency guidance.

Failures recorded during collection: {len(failures)}
"""


@app.local_entrypoint()
def main(repo_id: str = DEFAULT_REPO_ID, images_per_label: int = 16) -> None:
    result = train_and_upload.remote(repo_id=repo_id, images_per_label=images_per_label)
    print(json.dumps(result, indent=2))
