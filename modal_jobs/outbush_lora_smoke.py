"""Modal scaffold for Outbush AI LoRA/fine-tune jobs.

This is intentionally a safe scaffold: it validates Modal auth and remote
execution before expensive training is added.
"""

from __future__ import annotations

import modal


app = modal.App("outbush-ai-lora-smoke")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "huggingface_hub>=1.14.0",
)


@app.function(image=image, timeout=300)
def validate_environment() -> dict:
    import platform
    import sys

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "message": "Modal is ready for the Outbush LoRA training pipeline.",
    }


@app.local_entrypoint()
def main() -> None:
    print(validate_environment.remote())
