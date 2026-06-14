from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CACHE_PATH = Path(os.getenv("OUTBUSH_WEATHER_CACHE", "data/weather_cache.json"))

REGION_POINTS: dict[str, tuple[float, float, str]] = {
    "general australia": (-35.2809, 149.13, "Canberra"),
    "canberra": (-35.2809, 149.13, "Canberra"),
    "sydney": (-33.8688, 151.2093, "Sydney"),
    "blue mountains": (-33.7125, 150.3119, "Blue Mountains / Katoomba"),
    "katoomba": (-33.7125, 150.3119, "Blue Mountains / Katoomba"),
    "melbourne": (-37.8136, 144.9631, "Melbourne"),
    "brisbane": (-27.4698, 153.0251, "Brisbane"),
    "gold coast": (-28.0167, 153.4, "Gold Coast"),
    "cairns": (-16.9186, 145.7781, "Cairns"),
    "darwin": (-12.4634, 130.8456, "Darwin"),
    "alice springs": (-23.698, 133.8807, "Alice Springs"),
    "uluru": (-25.3444, 131.0369, "Uluru"),
    "perth": (-31.9523, 115.8613, "Perth"),
    "adelaide": (-34.9285, 138.6007, "Adelaide"),
    "hobart": (-42.8821, 147.3272, "Hobart"),
    "launceston": (-41.4332, 147.1441, "Launceston"),
    "broome": (-17.9614, 122.2359, "Broome"),
    "kimberley": (-17.9614, 122.2359, "Kimberley / Broome"),
    "snowy mountains": (-36.4559, 148.2636, "Snowy Mountains / Thredbo"),
    "thredbo": (-36.5059, 148.3043, "Thredbo"),
    "flinders ranges": (-31.4333, 138.5833, "Flinders Ranges"),
    "tasmania": (-42.8821, 147.3272, "Tasmania / Hobart"),
}

WEATHER_CODES = {
    0: "clear",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "rime fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    80: "rain showers",
    81: "heavy rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "severe thunderstorm with hail",
}

PROVIDERS = (
    (
        "Open-Meteo BOM ACCESS-G forecast API",
        "https://api.open-meteo.com/v1/bom",
        "https://open-meteo.com/en/docs/bom-api",
    ),
    (
        "Open-Meteo weather forecast API",
        "https://api.open-meteo.com/v1/forecast",
        "https://open-meteo.com/en/docs",
    ),
)


def resolve_region(region: str) -> dict[str, Any]:
    query = (region or "General Australia").strip().lower()
    for key, (lat, lon, label) in REGION_POINTS.items():
        if key in query or query in key:
            return {"query": region, "matched": label, "latitude": lat, "longitude": lon}
    lat, lon, label = REGION_POINTS["general australia"]
    return {"query": region, "matched": label, "latitude": lat, "longitude": lon}


def _cache_key(location: dict[str, Any]) -> str:
    return f"{location['matched']}|{location['latitude']:.3f}|{location['longitude']:.3f}"


def _load_cache() -> dict[str, Any]:
    try:
        return json.loads(CACHE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=2, sort_keys=True))
    tmp.replace(CACHE_PATH)


def _describe_events(days: list[dict[str, Any]]) -> list[str]:
    events: list[str] = []
    wet_days = [day for day in days if day.get("rain_mm", 0) >= 5 or day.get("rain_probability", 0) >= 60]
    heavy_days = [day for day in days if day.get("rain_mm", 0) >= 20]
    windy_days = [day for day in days if day.get("wind_kmh", 0) >= 35]
    hot_days = [day for day in days if day.get("max_c", 0) >= 32]
    very_hot_days = [day for day in days if day.get("max_c", 0) >= 38]
    cold_nights = [day for day in days if day.get("min_c", 99) <= 3]
    high_uv_days = [day for day in days if day.get("uv_index", 0) >= 8]
    storm_days = [day for day in days if "thunder" in day.get("summary", "")]
    if wet_days:
        events.append(f"Rain likely on {len(wet_days)} of the next {len(days)} days.")
    if heavy_days:
        events.append(f"Heavy rain signal on: {', '.join(day['date'] for day in heavy_days[:4])}.")
    if windy_days:
        events.append(f"Strong wind signal on: {', '.join(day['date'] for day in windy_days[:4])}.")
    if storm_days:
        events.append(f"Storm signal on: {', '.join(day['date'] for day in storm_days[:4])}.")
    if very_hot_days:
        events.append(f"Very hot day signal on: {', '.join(day['date'] for day in very_hot_days[:4])}.")
    elif hot_days:
        events.append(f"Hot day signal on: {', '.join(day['date'] for day in hot_days[:4])}.")
    if cold_nights:
        events.append(f"Cold night signal on: {', '.join(day['date'] for day in cold_nights[:4])}.")
    if high_uv_days:
        events.append("High UV is likely; plan sun protection and water.")
    return events or ["No major rain, wind, heat, cold, or storm signal stood out in the 10-day pack."]


def _normalise_daily(
    payload: dict[str, Any],
    location: dict[str, Any],
    provider: str,
    provider_url: str,
) -> dict[str, Any]:
    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    days: list[dict[str, Any]] = []
    for index, date in enumerate(times[:10]):
        code = _daily_value(daily, "weather_code", index, 0)
        days.append(
            {
                "date": date,
                "summary": WEATHER_CODES.get(int(code), f"code {code}"),
                "min_c": _daily_value(daily, "temperature_2m_min", index),
                "max_c": _daily_value(daily, "temperature_2m_max", index),
                "rain_mm": _daily_value(daily, "precipitation_sum", index),
                "rain_probability": _daily_value(daily, "precipitation_probability_max", index),
                "wind_kmh": _daily_value(daily, "wind_speed_10m_max", index),
                "uv_index": _daily_value(daily, "uv_index_max", index),
            }
        )
    rain_total = round(sum(day.get("rain_mm", 0) or 0 for day in days), 1)
    return {
        "mode": "weather_pack",
        "online": True,
        "cached": False,
        "provider": provider,
        "provider_url": provider_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "location": location,
        "days": days,
        "rain_summary": f"{rain_total} mm modelled across {len(days)} days.",
        "expected_events": _describe_events(days),
    }


def _daily_value(daily: dict[str, Any], key: str, index: int, default: float = 0) -> float:
    values = daily.get(key) or []
    try:
        value = values[index]
    except IndexError:
        return default
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return round(float(value), 1)
    return default


def _has_daily_values(payload: dict[str, Any]) -> bool:
    daily = payload.get("daily") or {}
    for key in (
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "wind_speed_10m_max",
    ):
        values = daily.get(key) or []
        if any(value is not None for value in values):
            return True
    return False


def fetch_weather_pack(region: str, refresh: bool = True) -> dict[str, Any]:
    location = resolve_region(region)
    cache = _load_cache()
    key = _cache_key(location)
    if not refresh and key in cache:
        data = dict(cache[key])
        data["cached"] = True
        data["online"] = False
        return data

    params = urlencode(
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "daily": ",".join(
                (
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "uv_index_max",
                )
            ),
            "timezone": "Australia/Sydney",
            "forecast_days": "10",
        }
    )
    errors: list[str] = []
    try:
        for provider, endpoint, provider_url in PROVIDERS:
            url = f"{endpoint}?{params}"
            request = Request(url, headers={"User-Agent": "Outbush-AI/0.1 offline-field-assistant"})
            try:
                with urlopen(request, timeout=8) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not _has_daily_values(payload):
                    errors.append(f"{provider}: empty daily values")
                    continue
                data = _normalise_daily(payload, location, provider, provider_url)
                cache[key] = data
                _save_cache(cache)
                return data
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
        raise RuntimeError("; ".join(errors) or "No provider returned daily values")
    except Exception as exc:
        if key in cache:
            data = dict(cache[key])
            data["online"] = False
            data["cached"] = True
            data["fetch_error"] = str(exc)
            return data
        return {
            "mode": "weather_pack",
            "online": False,
            "cached": False,
            "provider": "Open-Meteo forecast APIs",
            "provider_url": "https://open-meteo.com/",
            "fetch_error": str(exc),
            "location": location,
            "days": [],
            "rain_summary": "No 10-day pack is cached for this region yet.",
            "expected_events": ["Connect to the internet and sync this region before heading offline."],
        }
