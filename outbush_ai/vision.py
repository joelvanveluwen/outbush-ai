from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


VISION_PROMPT = """You are Outbush AI's local offline vision model for Australian bushwalkers.
Look at the image and return JSON only.
Use this schema:
{
  "subject_type": "snake|spider|fungus|plant|cloud_weather|animal|track_scene|unknown",
  "candidate_labels": ["short visual candidate"],
  "confidence": "low|medium|high",
  "visual_evidence": "brief visible evidence",
  "field_guidance": "brief practical next step"
}
If a snake-like body is visible, choose subject_type "snake".
If you cannot see the subject clearly, choose "unknown".
Do not say a plant, fungus, or animal is safe to touch or eat.
"""


def _default_cli() -> str:
    return os.getenv(
        "OUTBUSH_VISION_CLI",
        "/home/vanveluwen/llama-bin-b9616/llama-b9616/llama-mtmd-cli",
    )


def _default_model() -> str:
    return os.getenv(
        "OUTBUSH_VISION_MODEL",
        "/home/vanveluwen/models/smolvlm2-2.2b/SmolVLM2-2.2B-Instruct-Q4_K_M.gguf",
    )


def _default_mmproj() -> str:
    return os.getenv(
        "OUTBUSH_VISION_MMPROJ",
        "/home/vanveluwen/models/smolvlm2-2.2b/mmproj-SmolVLM2-2.2B-Instruct-Q8_0.gguf",
    )


def vision_status() -> dict[str, Any]:
    backend = os.getenv("OUTBUSH_VISION_BACKEND", "llama_cpp_mtmd")
    cli = _default_cli()
    model = _default_model()
    mmproj = _default_mmproj()
    active = (
        backend == "llama_cpp_mtmd"
        and Path(cli).exists()
        and Path(model).exists()
        and Path(mmproj).exists()
    )
    return {
        "backend": backend,
        "active": active,
        "cli": cli,
        "model": model,
        "mmproj": mmproj,
    }


def vision_available() -> bool:
    return bool(vision_status()["active"])


def classify_with_vision_model(image_bytes: bytes | None, content_type: str = "") -> dict[str, Any] | None:
    if not image_bytes or not vision_available():
        return None
    status = vision_status()
    suffix = _suffix_for_content_type(content_type)
    timeout = float(os.getenv("OUTBUSH_VISION_TIMEOUT", "120"))
    n_predict = os.getenv("OUTBUSH_VISION_N_PREDICT", "220")
    threads = os.getenv("OUTBUSH_VISION_THREADS", "4")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as image_file:
        image_file.write(image_bytes)
        image_file.flush()
        command = [
            status["cli"],
            "-m",
            status["model"],
            "--mmproj",
            status["mmproj"],
            "--image",
            image_file.name,
            "-p",
            VISION_PROMPT,
            "-n",
            n_predict,
            "--temp",
            "0.1",
            "-t",
            threads,
            "--no-mmproj-offload",
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return _with_debug_text({
                "available": True,
                "ok": False,
                "error": str(exc),
                "model_backend": "llama.cpp mtmd",
            }, "")

    raw_text = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    parsed = _parse_json_object(raw_text)
    if completed.returncode != 0:
        return _with_debug_text({
            "available": True,
            "ok": False,
            "error": f"vision model exited with code {completed.returncode}",
            "model_backend": "llama.cpp mtmd",
        }, raw_text)
    if not parsed:
        return _with_debug_text({
            "available": True,
            "ok": False,
            "error": "vision model returned no parseable JSON",
            "model_backend": "llama.cpp mtmd",
        }, raw_text)
    parsed["available"] = True
    parsed["ok"] = True
    parsed["model_backend"] = "llama.cpp mtmd"
    return _with_debug_text(parsed, raw_text)


def _suffix_for_content_type(content_type: str) -> str:
    lower = content_type.lower()
    if "webp" in lower:
        return ".webp"
    if "png" in lower:
        return ".png"
    if "jpeg" in lower or "jpg" in lower:
        return ".jpg"
    return ".img"


def _parse_json_object(text: str) -> dict[str, Any] | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = [fenced.group(1)] if fenced else []
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last > first:
        candidates.append(text[first : last + 1])
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return None


def _with_debug_text(data: dict[str, Any], raw_text: str) -> dict[str, Any]:
    debug = os.getenv("OUTBUSH_VISION_DEBUG", "").strip().lower()
    if debug in {"1", "true", "yes", "on"}:
        data["raw_text"] = raw_text[-1200:]
    return data
