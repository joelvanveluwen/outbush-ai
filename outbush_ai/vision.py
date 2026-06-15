from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import tarfile
import threading
from pathlib import Path
from urllib.request import urlretrieve
from typing import Any


VISION_PROMPT = """You are Outbush AI's local offline vision model for Australian bushwalkers.
Look at the image and return JSON only.
Use this schema:
{
  "subject_type": "snake|spider|fungus|plant|cloud_weather|animal|track_scene|unknown",
  "candidate_labels": ["unknown snake"],
  "confidence": "low|medium|high",
  "visual_evidence": "brief visible evidence",
  "field_guidance": "brief practical next step"
}
If a snake-like body is visible, choose subject_type "snake".
When a snake or spider is visible, compare against Australian danger labels:
yellow-bellied sea snake, red-bellied black snake, eastern brown snake,
western brown snake, tiger snake, coastal taipan, inland taipan,
Sydney funnel-web spider, redback spider.
Also allow non-danger-label snake candidates such as carpet python,
diamond python, spotted python, python-like snake, or unknown snake when the
body is heavy, tree-climbing, or strongly blotched/diamond patterned.
Also identify common Australian marine hazards, stinging or toxic plants,
cloud and storm cues, bush tucker candidates, and mushrooms when visible.
If a snake is visible but the species is uncertain, use "unknown snake" or
"python-like snake" rather than guessing a named species.
For red-bellied black snake, look for a glossy dark/black upper body and
red, pink, or orange-red lower flank/belly. Only if those cues are clear, use
"red-bellied black snake" as the first candidate label.
If the snake has tan, cream, brown, blotched, diamond, netted, or python-like
patterning and no visible red/orange lower flank, do not label it as a
red-bellied black snake.
For a heavy tree-climbing snake with diamond/blotched patterning, prefer
"carpet python", "diamond python", or "python-like snake".
If you cannot see the subject clearly, choose "unknown".
Do not say a plant, fungus, or animal is safe to touch or eat.
"""

LLAMA_TAG = "b9616"
SPACE_RUNTIME_ROOT = Path(os.getenv("OUTBUSH_SPACE_MODEL_DIR", "/tmp/outbush-ai-models"))
SPACE_LLAMA_ARCHIVE = f"llama-{LLAMA_TAG}-bin-ubuntu-x64.tar.gz"
SPACE_LLAMA_URL = f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_TAG}/{SPACE_LLAMA_ARCHIVE}"
SPACE_VISION_REPO = "openbmb/MiniCPM-V-4.6-gguf"
SPACE_VISION_MODEL_FILE = os.getenv("OUTBUSH_MINICPM_MODEL_FILE", "MiniCPM-V-4_6-Q4_K_M.gguf")
SPACE_VISION_MMPROJ_FILE = "mmproj-model-f16.gguf"
_SETUP_LOCK = threading.Lock()
_SETUP_ATTEMPTED = False
_SETUP_ERROR = ""
_WARMUP_STARTED = False


def _default_cli() -> str:
    return os.getenv(
        "OUTBUSH_VISION_CLI",
        str(SPACE_RUNTIME_ROOT / f"llama-{LLAMA_TAG}" / "llama-mtmd-cli")
        if _space_auto_setup_enabled()
        else "/home/vanveluwen/llama-bin-b9616/llama-b9616/llama-mtmd-cli",
    )


def _default_model() -> str:
    return os.getenv(
        "OUTBUSH_VISION_MODEL",
        str(SPACE_RUNTIME_ROOT / "minicpm-v-4.6" / SPACE_VISION_MODEL_FILE)
        if _space_auto_setup_enabled()
        else f"/home/vanveluwen/models/minicpm-v-4.6/{SPACE_VISION_MODEL_FILE}",
    )


def _default_mmproj() -> str:
    return os.getenv(
        "OUTBUSH_VISION_MMPROJ",
        str(SPACE_RUNTIME_ROOT / "minicpm-v-4.6" / SPACE_VISION_MMPROJ_FILE)
        if _space_auto_setup_enabled()
        else f"/home/vanveluwen/models/minicpm-v-4.6/{SPACE_VISION_MMPROJ_FILE}",
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
        "auto_setup": _space_auto_setup_enabled(),
        "setup_attempted": _SETUP_ATTEMPTED,
        "setup_error": _SETUP_ERROR,
    }


def vision_available() -> bool:
    if not bool(vision_status()["active"]) and _space_auto_setup_enabled():
        ensure_space_vision_runtime()
    return bool(vision_status()["active"])


def start_space_vision_warmup() -> None:
    global _WARMUP_STARTED
    if not _space_auto_setup_enabled() or _WARMUP_STARTED or vision_status()["active"]:
        return
    _WARMUP_STARTED = True
    thread = threading.Thread(target=ensure_space_vision_runtime, name="outbush-space-vision-warmup", daemon=True)
    thread.start()


def ensure_space_vision_runtime() -> bool:
    global _SETUP_ATTEMPTED, _SETUP_ERROR
    if not _space_auto_setup_enabled():
        return False
    with _SETUP_LOCK:
        if vision_status()["active"]:
            _SETUP_ATTEMPTED = True
            _SETUP_ERROR = ""
            return True
        _SETUP_ATTEMPTED = True
        try:
            _install_space_llama_cli()
            _install_space_vision_files()
            _SETUP_ERROR = ""
        except Exception as exc:  # pragma: no cover - depends on network/runtime
            _SETUP_ERROR = str(exc)
            return False
    return bool(vision_status()["active"])


def _space_auto_setup_enabled() -> bool:
    configured = os.getenv("OUTBUSH_AUTO_SETUP_VISION", "").strip().lower()
    if configured in {"1", "true", "yes", "on"}:
        return True
    if configured in {"0", "false", "no", "off"}:
        return False
    return bool(os.getenv("SPACE_ID") or os.getenv("HF_SPACE_ID") or os.getenv("SPACE_HOST"))


def _install_space_llama_cli() -> None:
    cli = Path(_default_cli())
    if cli.exists():
        return
    SPACE_RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    archive_path = SPACE_RUNTIME_ROOT / SPACE_LLAMA_ARCHIVE
    _download_if_missing(SPACE_LLAMA_URL, archive_path)
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(SPACE_RUNTIME_ROOT)
    cli.chmod(0o755)


def _install_space_vision_files() -> None:
    model_dir = Path(_default_model()).parent
    model_dir.mkdir(parents=True, exist_ok=True)
    for file_name in (SPACE_VISION_MODEL_FILE, SPACE_VISION_MMPROJ_FILE):
        url = f"https://huggingface.co/{SPACE_VISION_REPO}/resolve/main/{file_name}"
        _download_if_missing(url, model_dir / file_name)


def _download_if_missing(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_destination = destination.with_suffix(destination.suffix + ".tmp")
    if tmp_destination.exists():
        tmp_destination.unlink()
    urlretrieve(url, tmp_destination)
    tmp_destination.replace(destination)


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
    _clean_vision_result(parsed)
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


def _clean_vision_result(data: dict[str, Any]) -> None:
    labels = data.get("candidate_labels")
    if isinstance(labels, str):
        labels = [labels]
    if not isinstance(labels, list):
        data["candidate_labels"] = []
        return

    cleaned: list[str] = []
    seen: set[str] = set()
    instruction_fragments = (
        "short visual candidate",
        "using a specific species",
        "diagnostic features",
        "json only",
        "candidate label",
    )
    for label in labels:
        value = str(label).strip()
        lower = value.lower()
        if not value or any(fragment in lower for fragment in instruction_fragments):
            continue
        if lower in seen:
            continue
        seen.add(lower)
        cleaned.append(value)
    data["candidate_labels"] = cleaned


def _with_debug_text(data: dict[str, Any], raw_text: str) -> dict[str, Any]:
    debug = os.getenv("OUTBUSH_VISION_DEBUG", "").strip().lower()
    if debug in {"1", "true", "yes", "on"}:
        data["raw_text"] = raw_text[-1200:]
    return data
