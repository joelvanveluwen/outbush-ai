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
            red_bellied_cue = _red_bellied_black_snake_cue(rgb)
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
    if red_bellied_cue["cue"]:
        signals.append("red_bellied_black_snake_colour_cue")
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
        "red_bellied_black_snake_cue": red_bellied_cue,
        "summary": f"Local image check: {width}x{height}, {tone}, {colour}.",
    }


def _red_bellied_black_snake_cue(image: Any) -> dict[str, Any]:
    sample = image.copy()
    sample.thumbnail((96, 96))
    width, height = sample.size
    pixel_data = sample.get_flattened_data() if hasattr(sample, "get_flattened_data") else sample.getdata()
    pixels = list(pixel_data)
    if not pixels:
        return {"cue": False}

    dark_mask: list[bool] = []
    red_mask: list[bool] = []
    for red, green, blue in pixels:
        luminance = (0.2126 * red) + (0.7152 * green) + (0.0722 * blue)
        channel_max = max(red, green, blue)
        channel_min = min(red, green, blue)
        saturation = (channel_max - channel_min) / max(channel_max, 1)
        dark_mask.append(luminance < 75 and channel_max < 115)
        red_mask.append(red > 55 and red > green * 1.18 and red > blue * 1.12 and saturation > 0.23)

    total = float(len(pixels))
    dark_ratio = sum(dark_mask) / total
    red_ratio = sum(red_mask) / total
    upper_red_ratio = _vertical_red_ratio(red_mask, width, height, 0.0, 0.5)
    lower_red_ratio = _vertical_red_ratio(red_mask, width, height, 0.5, 1.0)
    adjacent_red_ratio = _adjacent_red_dark_ratio(red_mask, dark_mask, width, height)
    red_is_lower_flank_like = lower_red_ratio >= max(0.025, upper_red_ratio * 1.12)
    cue = (
        0.08 <= dark_ratio <= 0.96
        and 0.035 <= red_ratio <= 0.24
        and adjacent_red_ratio >= 0.012
        and red_is_lower_flank_like
    )
    return {
        "cue": cue,
        "dark_ratio": round(dark_ratio, 4),
        "red_ratio": round(red_ratio, 4),
        "upper_red_ratio": round(upper_red_ratio, 4),
        "lower_red_ratio": round(lower_red_ratio, 4),
        "adjacent_red_dark_ratio": round(adjacent_red_ratio, 4),
    }


def _vertical_red_ratio(red_mask: list[bool], width: int, height: int, start: float, end: float) -> float:
    y_start = max(0, min(height, int(height * start)))
    y_end = max(y_start + 1, min(height, int(height * end)))
    total = 0
    red_count = 0
    for y in range(y_start, y_end):
        row_start = y * width
        row = red_mask[row_start : row_start + width]
        total += len(row)
        red_count += sum(row)
    return red_count / float(total or 1)


def _adjacent_red_dark_ratio(red_mask: list[bool], dark_mask: list[bool], width: int, height: int) -> float:
    adjacent = 0
    for y in range(height):
        for x in range(width):
            index = y * width + x
            if not red_mask[index]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
                xx = x + dx
                yy = y + dy
                if 0 <= xx < width and 0 <= yy < height and dark_mask[yy * width + xx]:
                    adjacent += 1
                    break
    return adjacent / float(len(red_mask) or 1)
