from __future__ import annotations

import os
import re
from dataclasses import asdict
from pathlib import Path

from .content import CHECKLIST_SECTIONS, DANGER_CARDS, KNOWLEDGE_ITEMS, KnowledgeItem, Source
from .llm import generate_with_llama, llama_available
from .photo import analyse_photo
from .retrieval import get_index
from .species_model import classify_with_species_model, species_model_status
from .vision import classify_with_vision_model, vision_status
from .weather import fetch_weather_pack


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
    "sting",
    "stung",
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


def _source_dict(source: Source) -> dict:
    return asdict(source)


def _item_to_source(item: KnowledgeItem) -> dict:
    data = _source_dict(item.source)
    data["matched_item"] = item.title
    return data


def _risk_for_text(text: str, matches: list[KnowledgeItem]) -> str:
    lower = text.lower()
    if any(term in lower for term in CRITICAL_TERMS):
        return "critical"
    if any(term in lower for term in HIGH_TERMS):
        return "high"
    return "normal"


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
        f"Region: {region}\nQuestion: {message}\nLocal source notes:\n{context}\n<answer>"
    )
    model_text = generate_with_llama(llama_prompt)
    if model_text:
        footer = _deterministic_guardrail_footer(message)
        return f"{_safety_banner(risk)}\n\n{model_text}{footer}"

    lines = [_safety_banner(risk), ""]
    if not matches:
        lines.append(
            "I do not have a strong local match for that. Re-check your surroundings, "
            "avoid touching or eating unknown things, and use emergency services for "
            "injury, toxin exposure, severe weather exposure, or immediate danger."
        )
    else:
        lines.append("Most relevant offline notes:")
        for item in matches[:3]:
            lines.append(f"- {item.text}")
    footer = _deterministic_guardrail_footer(message).strip()
    if footer:
        lines.append(footer)
    return "\n".join(lines)


def _deterministic_guardrail_footer(message: str) -> str:
    lower = message.lower()
    lines: list[str] = []
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
    if "eat" in lower or "edible" in lower or "bush tucker" in lower:
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
    matches = get_index().search(f"{message} {region}", limit=4)
    risk = _risk_for_text(message, matches)
    return {
        "mode": "chat",
        "offline": True,
        "model_backend": "llama.cpp" if llama_available() else "deterministic_offline_fallback",
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
    species_confidence = str(species_result.get("confidence") if species_result else "").lower()
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

    if has_term(PHOTO_MUSHROOM_TERMS) or vision_subject == "fungus" or species_subject == "fungus":
        risk = "critical"
        if vision_subject != "fungus":
            add_candidate("Unknown wild mushroom or fungus", "high hazard match", "The note or filename mentions fungus/mushroom language.")
        care_notes.append(
            "Do not eat wild mushrooms. If anyone ate one, call 13 11 26 or 000 if seriously unwell."
        )
        sources.append(_source_dict(next(item for item in KNOWLEDGE_ITEMS if item.key == "mushrooms").source))
    if has_term(PHOTO_SNAKE_TERMS) or vision_subject == "snake" or species_subject == "snake":
        risk = "critical"
        if vision_subject != "snake":
            add_candidate("Possible snake or snake-like animal", "hazard match", "The note or filename mentions snake language.")
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
    if species_result and species_result.get("ok") and species_confidence in {"medium", "high"}:
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
    matches = get_index().search(topic, limit=4)
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
    matches = get_index().search(query or "bushwalking safety", limit=limit)
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


def _compose_encyclopedia_answer(query: str, matches: list[KnowledgeItem]) -> str:
    if not matches:
        return "I could not find a local match in the Australia field pack."
    context = "\n".join(f"- {item.title}: {item.text}" for item in matches[:6])
    prompt = (
        "You are Outbush AI. Answer from the local Australia field encyclopedia only. "
        "Be concise, mention uncertainty, and include practical bushwalking relevance.\n"
        f"Question: {query or 'What is useful here?'}\nSources:\n{context}\n<answer>"
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
    if any(word in lower for word in ("tropic", "darwin", "cairns", "kimberley", "monsoon")):
        profile = "Tropical north: expect heat, humidity, intense rain in wet season, lightning/storm risk, and cyclone-season planning needs."
    elif any(word in lower for word in ("alpine", "snowy", "tasmania", "blue mountains", "high country")):
        profile = "Alpine/tableland: conditions can shift quickly; cold exposure, wind, rain, and poor visibility can matter even on mild days."
    elif any(word in lower for word in ("desert", "arid", "red centre", "simpson", "flinders")):
        profile = "Arid interior: heat, limited water, exposure, and cold nights are the dominant planning hazards."
    elif any(word in lower for word in ("coast", "sydney", "brisbane", "melbourne", "perth", "adelaide")):
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


def health_status() -> dict:
    knowledge = get_index().summary()
    vision = vision_status()
    species = species_model_status()
    return {
        "status": "ok",
        "app": "outbush-ai",
        "offline_ready": True,
        "llama_configured": llama_available(),
        "llama_base_url": os.getenv("LLAMA_CPP_BASE_URL", ""),
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
                "name": os.getenv("OUTBUSH_TEXT_MODEL", "Qwen2.5 local GGUF via llama.cpp when enabled"),
                "role": "offline chat and RAG synthesis",
                "active": llama_available(),
            },
            {
                "name": os.getenv("OUTBUSH_SPECIES_MODEL", "Outbush dangerous-species classifier"),
                "role": "offline species triage for Australian dangerous animals",
                "active": species["active"],
                "labels": species["labels"],
            },
            {
                "name": os.getenv("OUTBUSH_PHOTO_MODEL", "SmolVLM2 local GGUF via llama.cpp mtmd"),
                "role": "offline photo triage",
                "active": vision["active"],
                "fallback": "Pillow local image heuristics",
            },
        ],
    }
