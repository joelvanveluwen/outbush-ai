from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:  # pragma: no cover - exercised only on stripped installs
    Image = None


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = ROOT / "models" / "outbush_dangerous_species_classifier.json"
BACKEND_NAME = "outbush field-tuned species classifier"


def _model_path() -> Path:
    return Path(os.getenv("OUTBUSH_SPECIES_MODEL_PATH", str(DEFAULT_MODEL_PATH)))


@lru_cache(maxsize=1)
def _load_model() -> dict[str, Any] | None:
    path = _model_path()
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            model = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    classes = model.get("classes")
    if not isinstance(classes, list) or not classes:
        return None
    return model


def species_model_status() -> dict[str, Any]:
    model = _load_model()
    return {
        "backend": BACKEND_NAME,
        "active": bool(model),
        "path": str(_model_path()),
        "labels": len(model.get("classes", [])) if model else 0,
        "repo_id": model.get("repo_id", "") if model else "",
        "trained_at": model.get("trained_at", "") if model else "",
    }


def species_model_available() -> bool:
    return bool(_load_model())


def classify_with_species_model(image_bytes: bytes | None, content_type: str = "") -> dict[str, Any] | None:
    if not image_bytes or not species_model_available():
        return None
    model = _load_model()
    if not model:
        return None
    try:
        features = extract_image_features(image_bytes)
    except ValueError as exc:
        return {
            "available": True,
            "ok": False,
            "error": str(exc),
            "model_backend": BACKEND_NAME,
        }
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in model.get("classes", []):
        centroid = item.get("centroid")
        if isinstance(centroid, list) and len(centroid) == len(features):
            scored.append((_cosine(features, centroid), item))
    if not scored:
        return {
            "available": True,
            "ok": False,
            "error": "species model has no compatible centroids",
            "model_backend": BACKEND_NAME,
        }
    scored.sort(key=lambda pair: pair[0], reverse=True)
    threshold_medium = float(model.get("confidence_threshold_medium", 0.88))
    threshold_high = float(model.get("confidence_threshold_high", 0.94))
    margin_medium = float(model.get("confidence_margin_medium", 0.015))
    margin_high = float(model.get("confidence_margin_high", 0.035))
    top_score, top_item = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    score_margin = top_score - second_score
    top_labels = [
        {
            "label": item.get("label", "unknown"),
            "score": round(score, 4),
            "risk": item.get("risk", "high"),
        }
        for score, item in scored[:3]
    ]
    confidence = "low"
    if top_score >= threshold_high and score_margin >= margin_high:
        confidence = "high"
    elif top_score >= threshold_medium and score_margin >= margin_medium:
        confidence = "medium"
    guidance = str(
        top_item.get(
            "field_guidance",
            "Keep distance, avoid handling, and treat image identification as uncertain.",
        )
    )
    evidence = (
        f"Compared the uploaded image with {int(model.get('training_examples', 0))} "
        f"licensed training examples across {len(model.get('classes', []))} labels."
    )
    return {
        "available": True,
        "ok": True,
        "model_backend": BACKEND_NAME,
        "subject_type": top_item.get("subject_type", "animal"),
        "candidate_labels": [top_item.get("label", "unknown")],
        "confidence": confidence,
        "score": round(top_score, 4),
        "score_margin": round(score_margin, 4),
        "top_matches": top_labels,
        "risk": top_item.get("risk", "high"),
        "hazard_group": top_item.get("hazard_group", ""),
        "visual_evidence": evidence,
        "field_guidance": guidance,
        "source": top_item.get("source", {}),
        "content_type": content_type,
    }


def extract_image_features(image_bytes: bytes) -> list[float]:
    if Image is None:
        raise ValueError("Pillow is not installed")
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size
            rgb = image.convert("RGB")
            rgb.thumbnail((96, 96))
            pixel_data = rgb.get_flattened_data() if hasattr(rgb, "get_flattened_data") else rgb.getdata()
            pixels = list(pixel_data)
    except Exception as exc:  # pragma: no cover - depends on malformed images
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


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
