from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def llama_available() -> bool:
    return bool(os.getenv("OUTBUSH_USE_LLAMA")) and bool(os.getenv("LLAMA_CPP_BASE_URL"))


def generate_with_llama(prompt: str, max_tokens: int = 280) -> str | None:
    if not llama_available():
        return None
    base_url = os.environ["LLAMA_CPP_BASE_URL"].rstrip("/")
    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": 0.2,
        "stop": ["</answer>", "\n\nUser:"],
    }
    request = urllib.request.Request(
        f"{base_url}/completion",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    content = data.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None
