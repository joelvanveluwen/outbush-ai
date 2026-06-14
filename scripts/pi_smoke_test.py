#!/usr/bin/env python3
"""Small smoke test for an Outbush AI HTTP server."""

from __future__ import annotations

import json
import os
import sys
import urllib.request


BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:7860"
REQUEST_TIMEOUT = float(os.getenv("OUTBUSH_SMOKE_TIMEOUT", "30"))


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE_URL + path, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def post(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    checks = {
        "health": get("/api/health"),
        "chat": post("/api/chat", {"message": "Can I eat this wild mushroom?", "region": "NSW"}),
        "firstaid": post("/api/firstaid", {"topic": "snake bite"}),
        "weather": post("/api/weather", {"region": "Blue Mountains", "cloud_note": "dark anvil cloud"}),
        "checklist": get("/api/checklist"),
        "encyclopedia": post("/api/encyclopedia", {"query": "Australian snakes", "limit": 3}),
    }
    assert checks["health"]["status"] == "ok", checks["health"]
    assert "do not eat wild mushrooms" in checks["chat"]["answer"].lower(), checks["chat"]["answer"]
    assert "triple zero" in " ".join(checks["firstaid"]["steps"]).lower(), checks["firstaid"]
    assert "live bom forecast" in checks["weather"]["pre_trip_note"].lower(), checks["weather"]
    assert "plb" in checks["checklist"]["export_text"].lower(), checks["checklist"]
    assert checks["encyclopedia"]["results"], checks["encyclopedia"]
    assert checks["encyclopedia"]["knowledge"]["backend"] == "sqlite", checks["encyclopedia"]["knowledge"]
    print(json.dumps({"base_url": BASE_URL, "checks": list(checks.keys()), "status": "ok"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
