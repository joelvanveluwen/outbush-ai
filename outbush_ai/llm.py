from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .vision import (
    LLAMA_TAG,
    SPACE_RUNTIME_ROOT,
    _SETUP_LOCK as _VISION_SETUP_LOCK,
    _install_space_llama_cli,
    _space_auto_setup_enabled,
)


TEXT_MODEL_REPO = "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF"
TEXT_MODEL_FILE = "NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf"
_TEXT_SETUP_LOCK = threading.Lock()
_TEXT_SETUP_ATTEMPTED = False
_TEXT_SETUP_ERROR = ""
_TEXT_SETUP_STAGE = "idle"
_TEXT_MODEL_BYTES = 0
_TEXT_MODEL_EXPECTED_BYTES = 0
_LAST_LLAMA_ERROR = ""
_TEXT_WARMUP_STARTED = False
_TEXT_PROCESS: subprocess.Popen | None = None


def llama_available() -> bool:
    base_url = _base_url()
    if not base_url:
        return False
    if not os.getenv("OUTBUSH_USE_LLAMA") and not _space_text_auto_setup_enabled():
        return False
    return _server_healthy(base_url, timeout=0.4)


def text_model_status() -> dict[str, Any]:
    base_url = _base_url()
    active = llama_available()
    return {
        "backend": "llama.cpp server",
        "active": active,
        "base_url": base_url,
        "auto_setup": _space_text_auto_setup_enabled(),
        "setup_attempted": _TEXT_SETUP_ATTEMPTED,
        "setup_error": _TEXT_SETUP_ERROR,
        "setup_stage": _TEXT_SETUP_STAGE,
        "cli": str(_default_text_server()),
        "model": str(_default_text_model()),
        "repo_id": os.getenv("OUTBUSH_TEXT_MODEL_REPO", TEXT_MODEL_REPO),
        "model_file": os.getenv("OUTBUSH_TEXT_MODEL_FILE", TEXT_MODEL_FILE),
        "model_bytes": _TEXT_MODEL_BYTES or _existing_size(_default_text_model()),
        "model_expected_bytes": _TEXT_MODEL_EXPECTED_BYTES,
        "last_generation_error": _LAST_LLAMA_ERROR,
        "pid": _TEXT_PROCESS.pid if _TEXT_PROCESS and _TEXT_PROCESS.poll() is None else None,
    }


def start_space_text_warmup() -> None:
    global _TEXT_WARMUP_STARTED
    if not _space_text_auto_setup_enabled() or _TEXT_WARMUP_STARTED or llama_available():
        return
    _TEXT_WARMUP_STARTED = True
    thread = threading.Thread(target=ensure_space_text_runtime, name="outbush-space-text-warmup", daemon=True)
    thread.start()


def ensure_space_text_runtime() -> bool:
    global _TEXT_SETUP_ATTEMPTED, _TEXT_SETUP_ERROR
    if not _space_text_auto_setup_enabled():
        return False
    with _TEXT_SETUP_LOCK:
        _TEXT_SETUP_ATTEMPTED = True
        if llama_available():
            _set_text_stage("ready")
            _TEXT_SETUP_ERROR = ""
            return True
        try:
            _set_text_stage("installing llama.cpp")
            with _VISION_SETUP_LOCK:
                _install_space_llama_cli()
            server = _default_text_server()
            if server.exists():
                server.chmod(0o755)
            _set_text_stage("downloading text model")
            _install_space_text_model()
            _set_text_stage("starting llama-server")
            _start_space_text_server()
            _set_text_stage("ready")
            _TEXT_SETUP_ERROR = ""
        except Exception as exc:  # pragma: no cover - depends on Space runtime/network
            _set_text_stage("error")
            _TEXT_SETUP_ERROR = str(exc)
            return False
    return llama_available()


def generate_with_llama(prompt: str, max_tokens: int = 280) -> str | None:
    _set_llama_error("")
    if not llama_available():
        start_space_text_warmup()
        _set_llama_error("llama health endpoint is not active")
        return None
    base_url = _base_url().rstrip("/")
    timeout = float(os.getenv("OUTBUSH_LLAMA_TIMEOUT", "120"))
    if os.getenv("OUTBUSH_LLAMA_USE_CHAT", "").strip().lower() in {"1", "true", "yes", "on"}:
        chat_payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "stop": ["\n\nUser:"],
        }
        chat_text = _post_llama_chat(base_url, chat_payload, timeout)
        if chat_text:
            return chat_text

    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": 0.2,
        "stop": ["\n\nUser:"],
    }
    request = urllib.request.Request(
        f"{base_url}/completion",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _set_llama_error(f"completion HTTP {exc.code}: {_read_error_body(exc)}")
        return None
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        _set_llama_error(f"completion request failed: {exc}")
        return None
    content = data.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    _set_llama_error(f"completion returned no content; keys={sorted(data.keys())}")
    return None


def _post_llama_chat(base_url: str, payload: dict[str, Any], timeout: float) -> str | None:
    request = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _set_llama_error(f"chat HTTP {exc.code}: {_read_error_body(exc)}")
        return None
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        _set_llama_error(f"chat request failed: {exc}")
        return None
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str) and content.strip():
        return content.strip()
    text = choices[0].get("text") if isinstance(choices[0], dict) else None
    if isinstance(text, str) and text.strip():
        return text.strip()
    _set_llama_error(f"chat returned no content; keys={sorted(data.keys())}")
    return None


def _space_text_auto_setup_enabled() -> bool:
    configured = os.getenv("OUTBUSH_AUTO_SETUP_TEXT", "").strip().lower()
    if configured in {"1", "true", "yes", "on"}:
        return True
    if configured in {"0", "false", "no", "off"}:
        return False
    return _space_auto_setup_enabled()


def _base_url() -> str:
    configured = os.getenv("LLAMA_CPP_BASE_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    if _space_text_auto_setup_enabled():
        return f"http://127.0.0.1:{_space_text_port()}"
    return ""


def _space_text_port() -> int:
    return int(os.getenv("OUTBUSH_TEXT_PORT", "8080"))


def _default_text_server() -> Path:
    configured = os.getenv("OUTBUSH_TEXT_CLI", "").strip()
    if configured:
        return Path(configured)
    if _space_text_auto_setup_enabled():
        return SPACE_RUNTIME_ROOT / f"llama-{LLAMA_TAG}" / "llama-server"
    return Path("/home/vanveluwen/llama-bin-b9616/llama-b9616/llama-server")


def _default_text_model() -> Path:
    configured = os.getenv("OUTBUSH_TEXT_MODEL_PATH", "").strip()
    if configured:
        return Path(configured)
    if _space_text_auto_setup_enabled():
        return SPACE_RUNTIME_ROOT / "nemotron-3-nano" / os.getenv("OUTBUSH_TEXT_MODEL_FILE", TEXT_MODEL_FILE)
    return Path(f"/home/vanveluwen/models/{os.getenv('OUTBUSH_TEXT_MODEL_FILE', TEXT_MODEL_FILE)}")


def _install_space_text_model() -> None:
    model_path = _default_text_model()
    repo_id = os.getenv("OUTBUSH_TEXT_MODEL_REPO", TEXT_MODEL_REPO)
    file_name = os.getenv("OUTBUSH_TEXT_MODEL_FILE", TEXT_MODEL_FILE)
    url = f"https://huggingface.co/{repo_id}/resolve/main/{file_name}"
    _download_text_model_if_missing(url, model_path)


def _start_space_text_server() -> None:
    global _TEXT_PROCESS
    base_url = _base_url()
    os.environ.setdefault("LLAMA_CPP_BASE_URL", base_url)
    os.environ.setdefault("OUTBUSH_USE_LLAMA", "1")
    if _server_healthy(base_url, timeout=1.0):
        return
    if _TEXT_PROCESS and _TEXT_PROCESS.poll() is None:
        _wait_for_server(base_url)
        return
    server = _default_text_server()
    model = _default_text_model()
    command = [
        str(server),
        "-m",
        str(model),
        "--host",
        "127.0.0.1",
        "--port",
        str(_space_text_port()),
        "-c",
        os.getenv("OUTBUSH_TEXT_CONTEXT", "2048"),
        "-t",
        os.getenv("OUTBUSH_TEXT_THREADS", "4"),
        "--no-webui",
    ]
    extra_args = os.getenv("OUTBUSH_TEXT_LLAMA_ARGS", "").strip()
    if extra_args:
        command.extend(shlex.split(extra_args))
    _TEXT_PROCESS = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _wait_for_server(base_url)


def _wait_for_server(base_url: str) -> None:
    _set_text_stage("waiting for llama-server")
    deadline = time.time() + float(os.getenv("OUTBUSH_TEXT_STARTUP_WAIT", "180"))
    while time.time() < deadline:
        if _server_healthy(base_url, timeout=1.0):
            return
        if _TEXT_PROCESS and _TEXT_PROCESS.poll() is not None:
            raise RuntimeError(f"llama-server exited with code {_TEXT_PROCESS.returncode}")
        time.sleep(2.0)
    raise TimeoutError("llama-server did not become healthy before timeout")


def _server_healthy(base_url: str, timeout: float = 0.6) -> bool:
    if not base_url:
        return False
    request = urllib.request.Request(f"{base_url.rstrip('/')}/health", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status < 500
    except (OSError, urllib.error.URLError, TimeoutError):
        return False


def _download_text_model_if_missing(url: str, destination: Path) -> None:
    global _TEXT_MODEL_BYTES, _TEXT_MODEL_EXPECTED_BYTES
    if destination.exists() and destination.stat().st_size > 0:
        _TEXT_MODEL_BYTES = destination.stat().st_size
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_destination = destination.with_suffix(destination.suffix + ".tmp")
    if tmp_destination.exists():
        tmp_destination.unlink()
    request = urllib.request.Request(url, method="GET")
    timeout = float(os.getenv("OUTBUSH_DOWNLOAD_TIMEOUT", "90"))
    with urllib.request.urlopen(request, timeout=timeout) as response:
        expected = response.headers.get("Content-Length")
        _TEXT_MODEL_EXPECTED_BYTES = int(expected) if expected and expected.isdigit() else 0
        _TEXT_MODEL_BYTES = 0
        with tmp_destination.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                _TEXT_MODEL_BYTES += len(chunk)
    tmp_destination.replace(destination)
    _TEXT_MODEL_BYTES = destination.stat().st_size


def _existing_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _set_text_stage(stage: str) -> None:
    global _TEXT_SETUP_STAGE
    _TEXT_SETUP_STAGE = stage


def _set_llama_error(message: str) -> None:
    global _LAST_LLAMA_ERROR
    _LAST_LLAMA_ERROR = message[:700]


def _read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read(700).decode("utf-8", errors="replace")
    except Exception:
        return ""
