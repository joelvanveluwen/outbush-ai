from __future__ import annotations

import os
import random
import re
from dataclasses import asdict
from pathlib import Path

from .content import CHECKLIST_SECTIONS, DANGER_CARDS, KNOWLEDGE_ITEMS, KnowledgeItem, Source
from .llm import generate_with_llama, llama_available, text_model_status
from .photo import analyse_photo
from .retrieval import get_index
from .species_model import classify_with_species_model, species_model_status
from .vision import classify_with_vision_model, vision_status
from .weather import fetch_weather_pack, weather_location_options


CRITICAL_TERMS = {
    "snake",
    "bite",
    "bitten",
    "mushroom",
    "fungus",
    "death cap",
    "crocodile",
    "jellyfish",
    "stonefish",
    "blue-ringed",
    "blue ringed",
    "taipan",
    "brown snake",
    "sea snake",
    "funnel-web",
    "funnel web",
    "box jellyfish",
    "irukandji",
    "ate",
    "eaten",
    "unconscious",
    "collapse",
    "bleeding",
    "chest pain",
    "can't breathe",
    "cannot breathe",
}

HIGH_TERMS = {
    "cliff",
    "cliffs",
    "lost",
    "heat",
    "dehydration",
    "hypothermia",
    "cold",
    "storm",
    "lightning",
    "flood",
    "fire",
    "bleeding",
    "exposure",
    "edge",
    "sting",
    "stung",
    "windy",
}

EMERGENCY_SYMPTOM_TERMS = {
    "unconscious",
    "collapse",
    "collapsing",
    "not breathing",
    "can't breathe",
    "cannot breathe",
    "breathing trouble",
    "chest pain",
    "severe bleeding",
}

PHOTO_MUSHROOM_TERMS = ("mushroom", "fungus", "fungi", "toadstool", "deathcap", "death cap")
PHOTO_SNAKE_TERMS = (
    "snake",
    "brown",
    "brown snake",
    "red belly black",
    "red-bellied black",
    "yellow bellied",
    "yellow-bellied",
    "sea snake",
    "tiger",
    "taipan",
    "adder",
    "python",
    "venom",
)
PHOTO_SPIDER_TERMS = (
    "spider",
    "funnel",
    "funnel web",
    "funnel-web",
    "redback",
    "red back",
    "mouse spider",
    "spider web",
    "webbing",
)
PHOTO_MARINE_TERMS = (
    "jellyfish",
    "irukandji",
    "blue bottle",
    "bluebottle",
    "blue-ringed octopus",
    "blue ringed octopus",
    "stonefish",
    "sea snake",
    "cone shell",
)
PHOTO_CLOUD_TERMS = (
    "cloud",
    "cumulonimbus",
    "storm",
    "anvil",
    "mammatus",
    "shelf",
    "dark sky",
)
PHOTO_PLANT_TERMS = ("plant", "leaf", "berry", "seed", "flower", "gympie", "stinging")
PHOTO_NEGATIVE_ANIMAL_TERMS = (
    "no animal",
    "no animals",
    "no snake",
    "no spider",
    "no wildlife",
    "no creature",
    "field kit",
    "backpack",
    "raspberry pi",
)
PHOTO_WORD_RE = re.compile(r"[a-z0-9]+")
RED_BELLIED_LABELS = ("red-bellied black snake", "red bellied black snake", "red belly black snake")
RED_BELLIED_GUARDRAIL = "red_bellied_colour_cue_absent"


def _source_dict(source: Source) -> dict:
    return asdict(source)


def _item_to_source(item: KnowledgeItem) -> dict:
    data = _source_dict(item.source)
    data["matched_item"] = item.title
    return data


def _risk_for_text(text: str, matches: list[KnowledgeItem]) -> str:
    lower = text.lower()
    if _is_redback_query(lower):
        if any(term in lower for term in EMERGENCY_SYMPTOM_TERMS):
            return "critical"
        return "high"
    if _is_funnel_web_query(lower):
        return "critical"
    if any(term in lower for term in CRITICAL_TERMS):
        return "critical"
    if any(term in lower for term in HIGH_TERMS) or _is_spider_hazard_query(lower):
        return "high"
    if matches and any(item.risk == "high" for item in matches[:2]):
        return "high"
    return "normal"


def _is_redback_query(lower: str) -> bool:
    return bool(re.search(r"\bred[\s-]?back\b|\bredback\b", lower))


def _is_funnel_web_query(lower: str) -> bool:
    return "funnel-web" in lower or "funnel web" in lower or "mouse spider" in lower


def _is_spider_hazard_query(lower: str) -> bool:
    if "spider" not in lower:
        return False
    hazard_words = ("danger", "venom", "bite", "bitten", "sting", "stung", "symptom", "first aid")
    return any(word in lower for word in hazard_words)


def _item_by_key(key: str) -> KnowledgeItem | None:
    return next((item for item in get_index().items if item.key == key), None)


def _dedupe_items(items: list[KnowledgeItem]) -> list[KnowledgeItem]:
    deduped: list[KnowledgeItem] = []
    seen: set[str] = set()
    for item in items:
        if item.key in seen:
            continue
        seen.add(item.key)
        deduped.append(item)
    return deduped


def _prioritize_hazard_matches(query: str, matches: list[KnowledgeItem], limit: int) -> list[KnowledgeItem]:
    lower = query.lower()
    priority_keys: list[str] = []
    if _is_redback_query(lower):
        if "bite" in lower or "bitten" in lower or "first aid" in lower:
            priority_keys.extend(["redback_first_aid", "redback_spider", "spider_bite"])
        else:
            priority_keys.extend(["redback_spider", "redback_first_aid", "spider_bite"])
    elif _is_funnel_web_query(lower):
        priority_keys.extend(["funnel_web_spider", "spider_bite"])
    elif _is_spider_hazard_query(lower):
        priority_keys.extend(["spider_bite", "redback_spider", "funnel_web_spider"])
    elif "snake" in lower and ("bite" in lower or "bitten" in lower or "first aid" in lower):
        priority_keys.append("snake_bite")
    elif "flood" in lower or "flooded" in lower or (
        any(term in lower for term in ("creek", "river", "causeway", "crossing"))
        and any(term in lower for term in ("cross", "rising", "rise", "turn back"))
    ):
        priority_keys.extend(["floodwater_turnback", "water_crossings", "warnings_before_offline"])
        if "rainforest" in lower or "dorrigo" in lower:
            priority_keys.append("rainforest_creek_tree_hazards")
    elif "lost" in lower or "off track" in lower or "off-track" in lower or "can't find the track" in lower:
        priority_keys.extend(["lost_stop_signal_shelter", "track_navigation", "emergency_orientation"])
    elif "no reception" in lower or "no phone" in lower or "out of coverage" in lower:
        priority_keys.extend(
            ["no_reception_plb_comms", "plb_trip_intentions", "trip_intentions_overdue_plan", "bushwalking_safety"]
        )
    elif any(term in lower for term in ("lightning", "thunder", "thunderstorm", "storm")):
        priority_keys.extend(["lightning_exposure_shelter", "thunderstorm_lightning", "warnings_before_offline"])
    elif "kosciuszko" in lower or "kosciusko" in lower or "alpine" in lower or "snowy mountains" in lower:
        priority_keys.extend(["kosciuszko_alpine_conditions", "alpine_weather", "group_turnaround_decision"])
    elif "rainforest" in lower or "dorrigo" in lower or "slippery" in lower or "leech" in lower:
        priority_keys.extend(["rainforest_creek_tree_hazards", "rainforest_stinging_tree", "water_crossings"])
    elif any(term in lower for term in ("cliff", "cliffs", "edge", "lookout")):
        priority_keys.extend(["warnings_before_offline", "group_turnaround_decision", "track_navigation"])
    elif any(term in lower for term in ("coast", "beach", "headland", "rockpool", "marine")):
        priority_keys.extend(["coastal_rockpool_marine_hazards", "sea_creature_first_aid", "warnings_before_offline"])
    elif "turn around" in lower or "turnaround" in lower or "turn back" in lower:
        priority_keys.extend(["group_turnaround_decision", "warnings_before_offline", "bushwalking_safety"])
    elif "heat" in lower or "water" in lower or "dehydration" in lower or "shade" in lower:
        priority_keys.extend(["remote_heat_water", "heat_illness", "group_turnaround_decision"])

    prioritized: list[KnowledgeItem] = []
    for key in priority_keys:
        item = _item_by_key(key)
        if item:
            prioritized.append(item)
    prioritized.extend(matches)
    return _dedupe_items(prioritized)[:limit]


def _safety_banner(risk: str) -> str:
    if risk == "critical":
        return (
            "Critical caution: treat this as uncertain and potentially serious. "
            "If someone is unconscious, not breathing, collapsing, severely bleeding, "
            "or rapidly worsening, call Triple Zero (000) now."
        )
    if risk == "high":
        return (
            "High caution: use this as field support, not certainty. Slow down, "
            "check the scene, and escalate early if symptoms or conditions worsen."
        )
    return (
        "Field note: this is offline guidance. Use situational awareness, current "
        "conditions, and official advice wherever available."
    )


def _compose_answer(message: str, region: str, matches: list[KnowledgeItem], risk: str) -> str:
    context = "\n".join(f"- {item.title}: {item.text}" for item in matches)
    llama_prompt = (
        "You are Outbush AI, an offline Australian bushwalking assistant. "
        "Be concise, practical, cautious, and source-aware. Never say a wild "
        "plant, animal, or mushroom is safe to eat or touch from a photo. "
        "Use 3-5 short bullets or short paragraphs. "
        "If the user asks whether something is dangerous, answer yes/no first, then explain the hazard and field actions. "
        "Do not answer with only yes or no. "
        "Use only the local source notes and do not mention unrelated animals. "
        "Prefer a direct model answer over copying source bullets. "
        "Keep the field disclaimer tone calm and do not over-explain limitations. "
        f"Region: {region}\nQuestion: {message}\nLocal source notes:\n{context}\nAnswer:"
    )
    max_tokens = int(os.getenv("OUTBUSH_CHAT_MAX_TOKENS", "120"))
    model_text = _clean_model_text(generate_with_llama(llama_prompt, max_tokens=max_tokens))
    model_text = _correct_high_risk_model_text(message, model_text)
    if model_text:
        footer = _deterministic_guardrail_footer(message)
        return f"{_safety_banner(risk)}\n\n{model_text}{footer}"

    lines = [
        _safety_banner(risk),
        "",
        "Local text model unavailable or timed out: I will not fabricate a deterministic chat answer. "
        "Start, sync, or give the local llama.cpp text model more time and ask again.",
    ]
    footer = _deterministic_guardrail_footer(message).strip()
    if footer:
        lines.append(footer)
    return "\n".join(lines)


def _clean_model_text(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = str(text).strip()
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
    closing_index = cleaned.lower().find("</think>")
    if closing_index >= 0:
        if closing_index < max(20, len(cleaned) // 4):
            cleaned = cleaned[closing_index + len("</think>") :]
        else:
            cleaned = cleaned[:closing_index]
    cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*(assistant\s*:\s*)?(answer\s*:\s*)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def _correct_high_risk_model_text(message: str, model_text: str | None) -> str | None:
    if not model_text:
        return None
    lower = message.lower()
    answer_lower = model_text.lower()
    pressure_question = re.search(r"\b(pressure|bandage|immobilisation|immobilization)\b", lower)
    if _is_redback_query(lower) and pressure_question:
        return (
            "No. Do not use pressure immobilisation for a likely redback bite. "
            "Wash the area, use a cold pack for pain and swelling, and call 13 11 26 "
            "or seek medical care if pain is severe, persistent, or spreads."
        )
    if "sea snake" in lower or (
        any(term in lower for term in ("marine", "beach", "sand", "shore"))
        and any(term in lower for term in ("animal", "snake", "creature", "stinger"))
    ):
        return (
            "Keep well back and do not handle it. Treat sea snakes and unknown marine animals as potentially dangerous, "
            "keep people and dogs away, and call 000 for any bite, severe sting symptoms, collapse, or breathing trouble."
        )
    if (
        any(term in lower for term in ("creek", "river", "causeway", "crossing"))
        and any(term in lower for term in ("rising", "rise", "flood", "flooded"))
        and any(term in lower for term in ("keep going", "continue", "cross", "turn back"))
        and ("keep going" in answer_lower or re.search(r"^\s*yes\b", answer_lower))
    ):
        return (
            "Turn back or wait on safe ground. Do not continue across a rising, fast, cloudy, "
            "or flood-affected creek. Keep the group together, avoid unstable crossings, and use "
            "a safer route or wait for conditions to drop."
        )
    if any(term in lower for term in ("cliff", "cliffs", "edge", "lookout", "headland")) and any(
        term in lower for term in ("photo", "wind", "windy", "selfie")
    ):
        return (
            "Say no and step back from the edge. In wind, keep everyone behind barriers or well "
            "back from cliff edges, stay together, and use a safer viewpoint for photos."
        )
    if ("no reception" in lower or "no phone" in lower or "out of coverage" in lower) and any(
        term in lower for term in ("before leaving", "what now", "before heading", "pre-walk", "prewalk")
    ):
        return (
            "Before leaving: cache maps and weather, share the route and return time, carry a charged phone, "
            "power bank, trip intentions, and a PLB or satellite messenger. Now: keep the group together, "
            "conserve battery, use the phone for GPS/Emergency+ if signal appears, and activate the PLB or call 000 "
            "if there is serious injury, exposure, or no safe way out."
        )
    return model_text


def _deterministic_guardrail_footer(message: str) -> str:
    lower = message.lower()
    lines: list[str] = []
    if _is_redback_query(lower):
        lines.append(
            "Redback field anchor: redbacks can cause severe pain; wash the bite, use a cold pack, "
            "call 13 11 26 or seek medical care for severe or persistent pain, and do not use pressure immobilisation."
        )
    if "snake" in lower and ("bite" in lower or "bitten" in lower or "first aid" in lower):
        lines.append(
            "Snake-bite field anchor: call 000, keep the person still, apply pressure immobilisation, "
            "and do not wash the bite or try to catch the snake."
        )
    if "flood" in lower or "flooded" in lower or (
        any(term in lower for term in ("creek", "river", "causeway", "crossing"))
        and any(term in lower for term in ("cross", "rising", "rise", "turn back"))
    ):
        lines.append(
            "Floodwater field anchor: do not cross rising, fast, cloudy, or flood-affected water; wait on safe ground or turn back."
        )
    if "crocodile" in lower or "croc" in lower:
        lines.append(
            "Crocodile field anchor: obey crocodile warning signs, keep well back from water edges, "
            "and turn back from flooded crossings or places where crocodiles may be present."
        )
    if "sea snake" in lower or (
        any(term in lower for term in ("marine", "beach", "sand", "shore"))
        and any(term in lower for term in ("animal", "snake", "creature", "stinger"))
    ):
        lines.append(
            "Marine animal field anchor: keep back from sea snakes and unknown marine animals, do not handle them, "
            "and call 000 for any bite, sting with severe symptoms, collapse, or breathing trouble."
        )
    if "rainforest" in lower or "dorrigo" in lower or "slippery" in lower:
        lines.append(
            "Rainforest field anchor: on slippery rainforest tracks and rising creeks, turn back early, "
            "avoid unstable crossings, watch for leeches and stinging trees, and stay on formed track."
        )
    if "lost" in lower or "off track" in lower or "off-track" in lower:
        lines.append(
            "Lost-track field anchor: stop, keep the group together, conserve battery, make yourself visible, and signal for help."
        )
    if "no reception" in lower or "no phone" in lower or "out of coverage" in lower:
        lines.append(
            "No-reception field anchor: carry offline maps, a charged phone/power bank, trip intentions, and a PLB or satellite messenger for remote routes."
        )
    if (
        "pre-walk" in lower
        or "prewalk" in lower
        or "before heading" in lower
        or "before leaving" in lower
        or "before departure" in lower
    ):
        lines.append(
            "Pre-walk field anchor: check weather, route, water, daylight, closures, phone battery, offline maps, "
            "trip intentions, and a PLB before heading out of coverage."
        )
    if any(term in lower for term in ("kosciuszko", "kosciusko", "alpine", "snowy mountains")) or (
        any(term in lower for term in ("cold", "windy", "wind", "snow", "alpine"))
        and any(term in lower for term in ("pack", "walking", "walk", "weather"))
    ):
        lines.append(
            "Alpine field anchor: for Kosciuszko and cold windy country, pack warm waterproof layers, navigation, "
            "food and water, and set a clear turnaround time before weather or daylight margins close."
        )
    if any(term in lower for term in ("lightning", "thunder", "thunderstorm")):
        lines.append(
            "Thunderstorm/lightning field anchor: seek substantial shelter early; leave exposed ridges, summits, beaches, "
            "cliff edges, exposed headlands, lone trees, water, and metal fences before the storm reaches you."
        )
    if any(term in lower for term in ("cliff", "cliffs", "edge", "lookout", "headland")) and any(
        term in lower for term in ("photo", "wind", "windy", "selfie")
    ):
        lines.append(
            "Cliff-edge field anchor: say no to photos near the edge; step back from cliff edges in wind, "
            "stay behind barriers, and use a safer viewpoint."
        )
    if "heat" in lower or "dehydration" in lower or "running out of water" in lower:
        lines.append(
            "Heat/water field anchor: stop in shade, ration effort, cool the person, and turn back before water or daylight margins are spent."
        )
    if "turn around" in lower or "turnaround" in lower or "turn back" in lower:
        lines.append(
            "Turnaround field anchor: decide by daylight, weather, water, group condition, navigation confidence, and the slowest person."
        )
    if "mushroom" in lower or "fung" in lower:
        lines.append(
            "Hard rule: do not eat wild mushrooms. If anyone has eaten one, call "
            "13 11 26, or 000 if seriously unwell."
        )
    if "weather" in lower or "forecast" in lower or "cloud" in lower:
        lines.append(
            "Weather limit: offline climate notes and cloud signs are not live forecasts. "
            "Before a trip, check BoM forecasts, fire danger, flood risk, and park closures."
        )
    if re.search(r"\b(eat|ate|eaten|edible)\b|\bbush tucker\b", lower):
        lines.append(
            "Foraging limit: do not rely on this app for consumption approval. Use a qualified local expert."
        )
    if not lines:
        return ""
    return "\n\n" + "\n".join(lines)


def ask_outbush(message: str, region: str = "General Australia") -> dict:
    message = (message or "").strip()
    if not message:
        message = "What should I check before a bushwalk?"
    matches = get_index().search(f"{message} {region}", limit=12)
    matches = _prioritize_hazard_matches(message, matches, 4)
    risk = _risk_for_text(message, matches)
    return {
        "mode": "chat",
        "offline": True,
        "model_backend": "llama.cpp" if llama_available() else "text_model_unavailable",
        "risk_level": risk,
        "answer": _compose_answer(message, region, matches, risk),
        "sources": [_item_to_source(item) for item in matches],
        "limits": [
            "Model output is uncertain and cannot replace emergency services, first-aid training, or professional care.",
            "Photo identification cannot prove an item is safe to eat or touch.",
            "Offline weather content is not a live forecast.",
        ],
    }


def identify_photo(
    file_name: str = "",
    note: str = "",
    image_bytes: bytes | None = None,
    content_type: str = "",
) -> dict:
    image_analysis = analyse_photo(image_bytes, file_name=file_name, content_type=content_type)
    species_result = classify_with_species_model(image_bytes, content_type=content_type)
    vision_result = classify_with_vision_model(image_bytes, content_type=content_type)
    file_stem = Path(file_name or "").stem
    text_signal = f"{file_stem} {note or ''}".lower()
    visual_signal = " ".join(image_analysis.get("visual_signals", [])).lower()
    signal_words = set(PHOTO_WORD_RE.findall(text_signal))
    sources: list[dict] = []
    care_notes: list[str] = [
        "Photo ID is uncertain. Keep distance and avoid handling or eating unknown wildlife, plants, or fungi based on this result."
    ]
    candidates: list[dict] = []
    risk = "normal"

    def add_candidate(label: str, confidence: str, reason: str) -> None:
        candidates.append({"label": label, "confidence": confidence, "reason": reason})

    def has_term(terms: tuple[str, ...]) -> bool:
        for term in terms:
            if " " in term or "-" in term:
                if term in text_signal:
                    return True
                continue
            if term in signal_words:
                return True
        return False

    vision_subject = _vision_subject(vision_result)
    vision_labels = _vision_labels(vision_result)
    species_subject = _vision_subject(species_result)
    species_labels = _vision_labels(species_result)
    red_bellied_cue = bool((image_analysis.get("red_bellied_black_snake_cue") or {}).get("cue"))
    species_result = _guard_red_bellied_model_result(species_result, red_bellied_cue)
    vision_result = _guard_red_bellied_model_result(vision_result, red_bellied_cue)
    species_subject = _vision_subject(species_result)
    species_labels = _vision_labels(species_result)
    species_confidence = str(species_result.get("confidence") if species_result else "").lower()
    vision_subject = _vision_subject(vision_result)
    vision_labels = _vision_labels(vision_result)
    species_snake_hint = _species_top_matches_snake(species_result)
    guarded_species_snake_hint = _is_guarded_red_bellied_result(species_result) and _vision_subject(species_result) == "snake"
    if species_confidence not in {"medium", "high"}:
        species_subject = ""
    if species_result and species_result.get("ok") and species_confidence in {"medium", "high"}:
        add_candidate(
            _species_candidate_label(species_result, species_labels),
            str(species_result.get("confidence") or "field-tuned model"),
            str(species_result.get("visual_evidence") or "Field-tuned dangerous-species classifier analyzed the image."),
        )
        species_risk = str(species_result.get("risk") or "").lower()
        if species_risk == "critical":
            risk = "critical"
        elif species_risk == "high" and risk == "normal":
            risk = "high"
        source = species_result.get("source")
        if isinstance(source, dict) and source.get("url"):
            sources.append(source)
        guidance = species_result.get("field_guidance")
        if guidance:
            care_notes.append(str(guidance))
    if _vision_conflicts_with_note(vision_subject, text_signal, species_confidence):
        vision_subject = ""
        vision_labels = []
    if vision_subject and vision_subject != "unknown":
        add_candidate(
            _vision_candidate_label(vision_subject, vision_labels),
            str(vision_result.get("confidence") or "vision model"),
            str(vision_result.get("visual_evidence") or "Local offline vision model analyzed the image."),
        )
    if red_bellied_cue and (vision_subject == "snake" or has_term(PHOTO_SNAKE_TERMS) or species_snake_hint):
        risk = "critical"
        add_candidate(
            "Possible red-bellied black snake",
            "visual cue",
            "Image analysis found dark-body and red/orange flank colour cues consistent with a red-bellied black snake. Treat this as uncertain field triage.",
        )
        care_notes.append("Keep clear of the snake. Use the snake-bite emergency flow for any suspected bite.")
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "red_bellied_black_snake").source))
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "snake_bite").source))

    if has_term(PHOTO_MUSHROOM_TERMS) or vision_subject == "fungus" or species_subject == "fungus":
        risk = "critical"
        if vision_subject != "fungus":
            add_candidate("Unknown wild mushroom or fungus", "high hazard match", "The note or filename mentions fungus/mushroom language.")
        care_notes.append(
            "Do not eat wild mushrooms. If anyone ate one, call 13 11 26 or 000 if seriously unwell."
        )
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "mushrooms").source))
    snake_signal = (
        has_term(PHOTO_SNAKE_TERMS)
        or vision_subject == "snake"
        or species_subject == "snake"
        or (guarded_species_snake_hint and not any(term in text_signal for term in PHOTO_NEGATIVE_ANIMAL_TERMS))
    )
    if snake_signal:
        risk = "critical"
        if vision_subject != "snake":
            if guarded_species_snake_hint:
                reason = (
                    "A local species model saw a snake-like subject, but the red-bellied black snake species label "
                    "was downgraded because the local colour cue was absent."
                )
            else:
                reason = "The note or filename mentions snake language."
            add_candidate("Possible snake or snake-like animal", "hazard match", reason)
        care_notes.append("Treat any suspected snake bite as an emergency and call 000.")
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "snake_bite").source))
    if has_term(PHOTO_SPIDER_TERMS) or vision_subject == "spider" or species_subject == "spider":
        risk = "high" if risk != "critical" else risk
        if vision_subject != "spider":
            add_candidate("Possible spider", "hazard match", "The note or filename mentions spider language.")
        care_notes.append("For suspected funnel-web or mouse spider bite, call 000 and use pressure immobilisation.")
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "spider_bite").source))
    if has_term(PHOTO_PLANT_TERMS) or vision_subject == "plant":
        risk = "high" if risk == "normal" else risk
        if vision_subject != "plant":
            add_candidate("Unknown plant", "uncertain", "The note or filename mentions plant language.")
        care_notes.append("Do not eat or touch unknown plants. Watch for stinging hairs, sap, berries, and skin irritation.")
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "stinging_plants").source))
    if has_term(PHOTO_CLOUD_TERMS) or "sky_or_cloud_context" in visual_signal or vision_subject == "cloud_weather":
        add_candidate("Cloud or sky condition", "educational only", "The note, filename, or image colours suggest cloud/weather context.")
        care_notes.append(
            "Cloud signs are not a forecast. If clouds are building vertically, darkening, or spreading into an anvil, consider shelter and check live BoM forecasts before departure."
        )
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "climate_averages").source))
    if has_term(PHOTO_MARINE_TERMS) or species_subject == "marine":
        risk = "critical" if any(term in text_signal for term in ("blue-ringed", "blue ringed", "stonefish", "sea snake", "irukandji", "box jelly")) else risk
        add_candidate("Possible marine hazard", "hazard match", "The note, classifier, or filename mentions a dangerous marine animal.")
        care_notes.append("For severe marine stings, blue-ringed octopus, stonefish, sea snake, or uncertainty with serious symptoms, call 000.")
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "sea_creature_first_aid").source))
    if "earth_bark_or_fungus_like_colours" in image_analysis.get("visual_signals", []):
        risk = "high" if risk == "normal" else risk
        add_candidate("Brown/orange field subject", "visual hint", "Local pixel analysis found bark, soil, leaf litter, or fungus-like tones.")
    if "plant_or_habitat_context" in image_analysis.get("visual_signals", []):
        add_candidate("Vegetation or habitat context", "visual hint", "Local pixel analysis found strong green tones.")
    if "sky_or_cloud_context" in image_analysis.get("visual_signals", []):
        add_candidate("Sky or cloud context", "visual hint", "Local pixel analysis found sky/cloud-like tones.")

    if not candidates:
        if image_analysis.get("image_present"):
            add_candidate(
                "Uploaded field photo",
                "image-only species ID unavailable",
                image_analysis["summary"] + " No offline wildlife vision model has classified the subject yet.",
            )
        else:
            add_candidate("Unknown field subject", "low", "No image or descriptive note was available.")
        care_notes.append(
            "Retake the photo in good light, include scale, avoid handling the subject, and describe where you found it."
        )

    deduped_sources = []
    seen = set()
    for source in sources:
        if source["url"] not in seen:
            seen.add(source["url"])
            deduped_sources.append(source)

    return {
        "mode": "photo",
        "offline": True,
        "model_backend": _photo_backend(species_result, vision_result),
        "risk_level": risk,
        "identification_status": "candidate hints only",
        "image_analysis": image_analysis,
        "species_model": species_result or {"available": False, "status": species_model_status()},
        "vision_model": vision_result or {"available": False, "status": vision_status()},
        "candidates": candidates,
        "care_notes": care_notes,
        "next_steps": [
            "Do not touch or eat the subject.",
            "If bitten, stung, or unwell, seek urgent help.",
            "Use this as triage; it is not a species certificate.",
        ],
        "sources": deduped_sources,
    }


def _vision_subject(vision_result: dict | None) -> str:
    if not vision_result or not vision_result.get("ok"):
        return ""
    subject = str(vision_result.get("subject_type") or "").strip().lower().replace("-", "_")
    aliases = {
        "cloud": "cloud_weather",
        "weather": "cloud_weather",
        "fungi": "fungus",
        "mushroom": "fungus",
        "snake_like": "snake",
    }
    return aliases.get(subject, subject)


def _vision_labels(vision_result: dict | None) -> list[str]:
    if not vision_result:
        return []
    labels = vision_result.get("candidate_labels")
    if isinstance(labels, list):
        return [str(label) for label in labels if str(label).strip()]
    if isinstance(labels, str) and labels.strip():
        return [labels.strip()]
    return []


def _guard_red_bellied_model_result(model_result: dict | None, red_bellied_cue: bool) -> dict | None:
    if not model_result or not model_result.get("ok") or _vision_subject(model_result) != "snake":
        return model_result
    labels = _vision_labels(model_result)
    if not any(_is_red_bellied_label(label) for label in labels):
        return model_result
    if red_bellied_cue:
        return model_result

    guarded = dict(model_result)
    guarded["candidate_labels"] = ["patterned snake or python-like animal"]
    guarded["confidence"] = "low"
    evidence = str(model_result.get("visual_evidence") or "Snake-like body visible.")
    guarded["visual_evidence"] = (
        f"{evidence} Local colour check did not find the red/orange lower-flank cue "
        "needed for a red-bellied black snake candidate."
    )
    guarded["field_guidance"] = (
        "Keep clear and do not handle it. Treat species ID as uncertain; use snake-bite first aid "
        "for any suspected bite."
    )
    guarded["guardrail"] = RED_BELLIED_GUARDRAIL
    guarded["original_candidate_labels"] = labels
    return guarded


def _is_guarded_red_bellied_result(model_result: dict | None) -> bool:
    return bool(model_result and model_result.get("guardrail") == RED_BELLIED_GUARDRAIL)


def _is_red_bellied_label(label: str) -> bool:
    normalised = label.lower().replace("-", " ")
    return any(candidate in normalised for candidate in RED_BELLIED_LABELS)


def _species_top_matches_snake(species_result: dict | None) -> bool:
    if not species_result or not species_result.get("ok"):
        return False
    labels: list[str] = []
    for match in species_result.get("top_matches") or []:
        if isinstance(match, dict):
            labels.append(str(match.get("label") or ""))
    labels.extend(_vision_labels(species_result))
    label_text = " ".join(labels).lower()
    return any(term in label_text for term in ("snake", "taipan", "adder", "python"))


def _vision_candidate_label(subject: str, labels: list[str]) -> str:
    if labels:
        return f"Vision candidate: {labels[0]}"
    names = {
        "snake": "Vision candidate: snake or snake-like animal",
        "spider": "Vision candidate: spider",
        "fungus": "Vision candidate: fungus or mushroom",
        "plant": "Vision candidate: plant",
        "cloud_weather": "Vision candidate: cloud or sky condition",
        "animal": "Vision candidate: animal",
        "track_scene": "Vision candidate: track or bush scene",
    }
    return names.get(subject, "Vision candidate: unknown field subject")


def _vision_conflicts_with_note(vision_subject: str, text_signal: str, species_confidence: str) -> bool:
    if vision_subject not in {"snake", "spider", "animal", "marine"}:
        return False
    if species_confidence in {"medium", "high"}:
        return False
    return any(term in text_signal for term in PHOTO_NEGATIVE_ANIMAL_TERMS)


def _species_candidate_label(species_result: dict, labels: list[str]) -> str:
    label = labels[0] if labels else str(species_result.get("hazard_group") or "dangerous species")
    score = species_result.get("score")
    if isinstance(score, float):
        return f"Field-tuned candidate: {label} ({score:.2f})"
    return f"Field-tuned candidate: {label}"


def _photo_backend(species_result: dict | None, vision_result: dict | None) -> str:
    backends = []
    species_confidence = str(species_result.get("confidence") if species_result else "").lower()
    if species_result and species_result.get("ok") and (
        species_confidence in {"medium", "high"} or _is_guarded_red_bellied_result(species_result)
    ):
        backends.append(str(species_result.get("model_backend") or "species classifier"))
    if vision_result and vision_result.get("ok"):
        backends.append(str(vision_result.get("model_backend") or "vision model"))
    return " + ".join(backends) if backends else "offline_image_heuristics"


def danger_cards() -> list[dict]:
    cards = []
    for card in DANGER_CARDS:
        data = dict(card)
        data["source"] = _source_dict(card["source"])
        cards.append(data)
    return cards


def first_aid_flow(topic: str) -> dict:
    topic = (topic or "").strip()
    matches = get_index().search(topic, limit=8)
    matches = _prioritize_first_aid_matches(topic, matches)
    risk = _risk_for_text(topic, matches)
    return {
        "mode": "first_aid",
        "topic": topic or "general",
        "risk_level": risk,
        "banner": _safety_banner(risk),
        "steps": [item.text for item in matches[:4]]
        or [
            "Stop and check for immediate danger.",
            "Call 000 for life-threatening symptoms or major injury.",
            "Use first-aid training and local emergency advice.",
        ],
        "do_not": [
            "Do not delay emergency care because the app is available.",
            "Do not rely on photo ID to decide if something is safe.",
            "Do not eat wild mushrooms.",
        ],
        "sources": [_item_to_source(item) for item in matches],
    }


def _prioritize_first_aid_matches(topic: str, matches: list[KnowledgeItem]) -> list[KnowledgeItem]:
    lower = topic.lower()
    priority_keys: list[str] = []
    if "snake" in lower and ("bite" in lower or "bitten" in lower):
        priority_keys.append("snake_bite")
    if "funnel" in lower or "mouse spider" in lower:
        priority_keys.append("spider_bite")
    if "redback" in lower or "red back" in lower:
        priority_keys.append("redback_first_aid")
    if "mushroom" in lower or "fungus" in lower or "ate" in lower or "eaten" in lower:
        priority_keys.append("mushrooms")
        priority_keys.append("poisoning")

    prioritized = [_item_by_key(key) for key in priority_keys]
    return _dedupe_items([item for item in prioritized if item] + matches)[:4]


def build_checklist() -> dict:
    export_text = "\n\n".join(
        [section["title"] + "\n" + "\n".join(f"[ ] {item}" for item in section["items"]) for section in CHECKLIST_SECTIONS]
    )
    return {
        "mode": "checklist",
        "title": "Outbush pre-walk checklist",
        "sections": CHECKLIST_SECTIONS,
        "export_text": export_text,
        "sources": [_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "bushwalking_safety").source)],
    }


def encyclopedia_search(query: str, limit: int = 6) -> dict:
    query = (query or "").strip()
    search_limit = max(limit, 12)
    matches = get_index().search(query or "bushwalking safety", limit=search_limit)
    matches = _prioritize_hazard_matches(query, matches, limit)
    answer = _compose_encyclopedia_answer(query, matches)
    return {
        "mode": "encyclopedia",
        "query": query,
        "offline": True,
        "model_backend": "llama.cpp" if llama_available() else "local_rag_synthesis",
        "knowledge": get_index().summary(),
        "answer": answer,
        "results": [
            {
                "key": item.key,
                "title": item.title,
                "text": item.text,
                "risk": item.risk,
                "tags": list(item.tags),
                "source": _item_to_source(item),
            }
            for item in matches
        ],
    }


def random_knowledge() -> dict:
    index = get_index()
    item = random.choice(index.items)
    return {
        "mode": "encyclopedia_random",
        "offline": True,
        "model_backend": "local_rag_synthesis",
        "knowledge": index.summary(),
        "answer": f"{item.title}: {item.text}",
        "results": [
            {
                "key": item.key,
                "title": item.title,
                "text": item.text,
                "risk": item.risk,
                "tags": list(item.tags),
                "source": _item_to_source(item),
            }
        ],
    }


def _compose_encyclopedia_answer(query: str, matches: list[KnowledgeItem]) -> str:
    if not matches:
        return "I could not find a local match in the Australia field pack."
    context = "\n".join(f"- {item.title}: {item.text}" for item in matches[:6])
    prompt = (
        "You are Outbush AI. Answer from the local Australia field encyclopedia only. "
        "Be concise, mention uncertainty, and include practical bushwalking relevance.\n"
        f"Question: {query or 'What is useful here?'}\nSources:\n{context}\nAnswer:"
    )
    model_text = generate_with_llama(prompt, max_tokens=220)
    if model_text:
        return model_text
    lead = f"I found {len(matches)} local encyclopedia match{'es' if len(matches) != 1 else ''}."
    bullets = "\n".join(f"- {item.title}: {item.text}" for item in matches[:3])
    return f"{lead}\n{bullets}"


def weather_advice(region: str = "General Australia", cloud_note: str = "", refresh_live: bool = False) -> dict:
    region = (region or "General Australia").strip()
    note = (cloud_note or "").strip()
    lower = f"{region} {note}".lower()
    if any(word in lower for word in ("tropic", "darwin", "cairns", "kimberley", "monsoon", "kakadu", "daintree")):
        profile = "Tropical north: expect heat, humidity, intense rain in wet season, lightning/storm risk, and cyclone-season planning needs."
    elif any(word in lower for word in ("alpine", "snowy", "tasmania", "blue mountains", "high country", "kosciuszko", "kosciusko", "thredbo")):
        profile = "Alpine/tableland: conditions can shift quickly; cold exposure, wind, rain, and poor visibility can matter even on mild days."
    elif any(word in lower for word in ("desert", "arid", "red centre", "simpson", "flinders", "uluru", "karijini")):
        profile = "Arid interior: heat, limited water, exposure, and cold nights are the dominant planning hazards."
    elif any(word in lower for word in ("coast", "sydney", "brisbane", "melbourne", "perth", "adelaide", "moonee", "coffs", "beach")):
        profile = "Coastal/temperate: changeable fronts, storms, wind, UV, and rapid temperature shifts can still make short walks risky."
    else:
        profile = "General Australia: plan for heat, UV, cold exposure, rain, wind, limited water, and fast-changing local conditions."
    cloud_hint = "No cloud note supplied."
    if note:
        if re.search(r"anvil|cumulonimbus|tower|dark|shelf|mammatus|storm", note, re.I):
            cloud_hint = "Cloud note suggests possible storm development, but this is not a live forecast. Treat it as an observation only and seek shelter if conditions worsen."
        else:
            cloud_hint = "Cloud note recorded. This app can discuss cloud signs, but it cannot provide a live forecast."
    pack = fetch_weather_pack(region, refresh=refresh_live)
    return {
        "mode": "weather",
        "region": region,
        "risk_level": "normal",
        "profile": profile,
        "cloud_read": cloud_hint,
        "pre_trip_note": "Before departure, check live BoM forecast, fire danger, flood risk, park status, and track conditions.",
        "weather_pack": pack,
        "sources": [
            _source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "climate_averages").source),
            _source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "climate_regions").source),
        ],
    }


def weather_locations() -> dict:
    return {
        "mode": "weather_locations",
        "count": len(weather_location_options()),
        "locations": weather_location_options(),
    }


def health_status() -> dict:
    knowledge = get_index().summary()
    text = text_model_status()
    vision = vision_status()
    species = species_model_status()
    return {
        "status": "ok",
        "app": "outbush-ai",
        "offline_ready": True,
        "llama_configured": text["active"],
        "llama_base_url": text["base_url"],
        "text_model": text,
        "knowledge_items": knowledge["items"],
        "knowledge_backend": knowledge["backend"],
        "knowledge_db_path": knowledge["db_path"],
        "knowledge_fts_enabled": knowledge["fts_enabled"],
        "vision_configured": vision["active"],
        "vision_backend": vision["backend"],
        "vision_model_path": vision["model"],
        "species_model_configured": species["active"],
        "species_model_backend": species["backend"],
        "species_model_path": species["path"],
        "species_model_labels": species["labels"],
        "models": [
            {
                "name": os.getenv("OUTBUSH_TEXT_MODEL", "NVIDIA Nemotron 3 Nano 4B local GGUF via llama.cpp when enabled"),
                "role": "offline chat and RAG synthesis",
                "active": text["active"],
                "path": text["model"],
            },
            {
                "name": os.getenv("OUTBUSH_SPECIES_MODEL", "Outbush dangerous-species classifier"),
                "role": "offline species triage for Australian dangerous animals",
                "active": species["active"],
                "labels": species["labels"],
            },
            {
                "name": os.getenv("OUTBUSH_PHOTO_MODEL", "OpenBMB MiniCPM-V 4.6 local GGUF via llama.cpp mtmd"),
                "role": "offline photo triage",
                "active": vision["active"],
                "fallback": "Pillow local image heuristics",
            },
        ],
    }
