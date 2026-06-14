from __future__ import annotations

from io import BytesIO
from typing import Any

try:
    from PIL import Image, ImageStat
except ImportError:  # pragma: no cover - exercised only on stripped installs
    Image = None
    ImageStat = None


def _tone(value: float) -> str:
    if value < 55:
        return "very dark"
    if value < 105:
        return "dim"
    if value > 215:
        return "very bright"
    if value > 170:
        return "bright"
    return "balanced"


def _colour_name(red: float, green: float, blue: float) -> str:
    channels = {"red": red, "green": green, "blue": blue}
    dominant = max(channels, key=channels.get)
    if green > red * 1.15 and green > blue * 1.15:
        return "green / vegetation-heavy"
    if blue > red * 1.15 and blue > green * 1.05:
        return "blue / sky-heavy"
    if red > 120 and green > 80 and blue < 90:
        return "orange-brown / bark-soil-fungus tones"
    if abs(red - green) < 12 and abs(green - blue) < 12:
        return "neutral / grey-white"
    return f"{dominant}-leaning"


def analyse_photo(image_bytes: bytes | None, file_name: str = "", content_type: str = "") -> dict[str, Any]:
    if not image_bytes:
        return {
            "image_present": False,
            "file_name": file_name,
            "content_type": content_type,
            "summary": "No image was uploaded.",
            "visual_signals": [],
        }
    if Image is None or ImageStat is None:
        return {
            "image_present": True,
            "file_name": file_name,
            "content_type": content_type,
            "bytes": len(image_bytes),
            "summary": "Image received, but Pillow is not installed so local pixel analysis is unavailable.",
            "visual_signals": ["image_uploaded"],
        }

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size
            mode = image.mode
            rgb = image.convert("RGB")
            sample = rgb.resize((64, 64))
            stat = ImageStat.Stat(sample)
            red, green, blue = stat.mean[:3]
            brightness = (red + green + blue) / 3
    except Exception as exc:  # pragma: no cover - depends on malformed binary data
        return {
            "image_present": True,
            "file_name": file_name,
            "content_type": content_type,
            "bytes": len(image_bytes),
            "decode_error": str(exc),
            "summary": "The upload arrived, but it could not be decoded as a normal image.",
            "visual_signals": ["image_decode_failed"],
        }

    colour = _colour_name(red, green, blue)
    tone = _tone(brightness)
    signals: list[str] = ["image_uploaded", colour, tone]
    if "green" in colour:
        signals.append("plant_or_habitat_context")
    if "blue" in colour:
        signals.append("sky_or_cloud_context")
    if "orange-brown" in colour:
        signals.append("earth_bark_or_fungus_like_colours")
    if width < 500 or height < 500:
        signals.append("low_detail")
    if tone in {"very dark", "very bright"}:
        signals.append("hard_to_read_lighting")

    return {
        "image_present": True,
        "file_name": file_name,
        "content_type": content_type,
        "bytes": len(image_bytes),
        "dimensions": {"width": width, "height": height},
        "mode": mode,
        "average_rgb": {"red": round(red), "green": round(green), "blue": round(blue)},
        "brightness": tone,
        "dominant_colour": colour,
        "visual_signals": signals,
        "summary": f"Local image check: {width}x{height}, {tone}, {colour}.",
    }
