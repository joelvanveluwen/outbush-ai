#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "models" / "vision_training_manifest.json"
OUT_JSON = ROOT / "docs" / "snake_photo_assessment.json"
OUT_MD = ROOT / "docs" / "snake_photo_assessment.md"
CACHE_DIR = ROOT / ".cache" / "snake_photo_eval"
DEFAULT_ENDPOINT = "http://vanveluwen-pi5:7860"

SNAKE_LABELS = (
    "red-bellied black snake",
    "eastern brown snake",
    "western brown snake",
    "tiger snake",
    "yellow-bellied sea snake",
    "coastal taipan",
    "common death adder",
    "carpet python",
)


def pick_examples() -> list[dict]:
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))
    examples = []
    for label in SNAKE_LABELS:
        match = next(item for item in items if item.get("label") == label and item.get("photo_url"))
        examples.append(match)
    return examples


def download(url: str, label: str, timeout: float) -> tuple[bytes, str]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    cache_path = CACHE_DIR / f"{label.replace(' ', '_')}-{digest}.bin"
    meta_path = CACHE_DIR / f"{label.replace(' ', '_')}-{digest}.json"
    if cache_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return cache_path.read_bytes(), str(meta.get("content_type", ""))

    last_error: Exception | None = None
    for attempt in range(1, 4):
        request = Request(url, headers={"User-Agent": "OutbushAI/1.0 snake-photo-evaluator"})
        try:
            with urlopen(request, timeout=timeout) as response:
                content = response.read()
                content_type = response.headers.get("Content-Type", "")
            cache_path.write_bytes(content)
            meta_path.write_text(json.dumps({"url": url, "content_type": content_type}, indent=2), encoding="utf-8")
            return content, content_type
        except (OSError, URLError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 * attempt)
    raise RuntimeError(f"could not download {url}: {last_error}")


def post_multipart(
    base_url: str,
    image_bytes: bytes,
    file_name: str,
    content_type: str,
    note: str,
    timeout: float,
) -> dict:
    boundary = f"----outbush-{uuid.uuid4().hex}"
    parts: list[bytes] = []
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{file_name}"\r\n'
            f"Content-Type: {content_type or 'application/octet-stream'}\r\n\r\n"
        ).encode("utf-8")
        + image_bytes
        + b"\r\n"
    )
    parts.append(
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="note"\r\n\r\n'
            f"{note}\r\n"
        ).encode("utf-8")
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)
    request = Request(
        f"{base_url.rstrip('/')}/api/photo",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(body))},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def labels_from_response(response: dict) -> str:
    labels = [candidate.get("label", "") for candidate in response.get("candidates", [])]
    labels.extend(response.get("vision_model", {}).get("candidate_labels", []) or [])
    labels.extend(response.get("species_model", {}).get("candidate_labels", []) or [])
    return " ".join(labels).lower()


def assess(expected: str, response: dict) -> dict:
    joined = labels_from_response(response)
    expected_hit = expected in joined
    snake_hit = "snake" in joined or "python" in joined or "adder" in joined or response.get("risk_level") == "critical"
    if expected == "carpet python":
        expected_hit = "python" in joined or expected_hit
    return {
        "expected_hit": expected_hit,
        "snake_or_safe_hazard_hit": snake_hit,
        "pass": expected_hit or snake_hit,
        "joined_labels": joined,
    }


def write_reports(results: list[dict], endpoint: str) -> None:
    OUT_JSON.write_text(json.dumps({"endpoint": endpoint, "results": results}, indent=2), encoding="utf-8")
    lines = [
        "# Snake Photo Assessment",
        "",
        f"- Endpoint: `{endpoint}`",
        f"- Run at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Passed: `{sum(1 for item in results if item['assessment']['pass'])}/{len(results)}`",
        "",
        "| # | Expected | Backend | Risk | Candidate labels | Assessment | Source photo |",
        "|---:|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(results, 1):
        labels = item["assessment"]["joined_labels"].replace("|", "/")
        status = "exact" if item["assessment"]["expected_hit"] else ("hazard" if item["assessment"]["pass"] else "review")
        lines.append(
            f"| {index} | {item['expected_label']} | {item['model_backend']} | {item['risk_level']} | "
            f"{labels} | {status} | [iNaturalist]({item['uri']}) |"
        )
    lines.extend(["", "## Notes", ""])
    for index, item in enumerate(results, 1):
        vision = item.get("vision_model", {})
        species = item.get("species_model", {})
        lines.extend(
            [
                f"### {index}. {item['expected_label']}",
                "",
                f"- Vision: `{vision.get('candidate_labels', [])}` confidence `{vision.get('confidence', '-')}`",
                f"- Species classifier: `{species.get('candidate_labels', [])}` confidence `{species.get('confidence', '-')}`",
                f"- Guardrail: `{vision.get('guardrail', '-')}`",
                f"- Attribution: {item.get('attribution', '-')}",
                "",
            ]
        )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--download-timeout", type=float, default=90)
    parser.add_argument("--request-timeout", type=float, default=360)
    args = parser.parse_args()
    results = []
    for example in pick_examples():
        try:
            image_bytes, content_type = download(example["photo_url"], example["label"], args.download_timeout)
            suffix = mimetypes.guess_extension(content_type.split(";")[0]) or Path(example["photo_url"]).suffix or ".jpg"
            file_name = f"{example['label'].replace(' ', '_')}{suffix}"
            response = post_multipart(
                args.endpoint,
                image_bytes,
                file_name,
                content_type,
                f"test photo: {example['label']}",
                args.request_timeout,
            )
            assessment = assess(example["label"], response)
        except Exception as exc:
            response = {
                "model_backend": "request_failed",
                "risk_level": "unknown",
                "candidates": [],
                "vision_model": {"error": str(exc)},
                "species_model": {},
            }
            assessment = {
                "expected_hit": False,
                "snake_or_safe_hazard_hit": False,
                "pass": False,
                "joined_labels": "",
                "error": str(exc),
            }
        results.append(
            {
                "expected_label": example["label"],
                "photo_url": example["photo_url"],
                "uri": example.get("uri", ""),
                "attribution": example.get("attribution", ""),
                "model_backend": response.get("model_backend", ""),
                "risk_level": response.get("risk_level", ""),
                "candidates": response.get("candidates", []),
                "vision_model": response.get("vision_model", {}),
                "species_model": response.get("species_model", {}),
                "assessment": assessment,
            }
        )
        status = "pass" if assessment["pass"] else "review"
        print(f"{len(results):02d}. {example['label']} -> {status}", flush=True)
        write_reports(results, args.endpoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
