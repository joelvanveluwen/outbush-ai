#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENDPOINT = "http://vanveluwen-pi5:7860"
OUT_JSON = ROOT / "docs" / "survival_question_assessment.json"
OUT_MD = ROOT / "docs" / "survival_question_assessment.md"

QUESTIONS = [
    {
        "region": "Blue Mountains",
        "question": "We lost the track in the Blue Mountains and the group is getting tired. What should we do now?",
        "expect": ("stop", "together", "visible", "help"),
    },
    {
        "region": "Kosciuszko",
        "question": "What should I pack and check before walking to Kosciuszko in cold windy weather?",
        "expect": ("warm", "waterproof", "weather", "turnaround"),
    },
    {
        "region": "Dorrigo",
        "question": "Rainforest creek is rising and the track is slippery near Dorrigo. Keep going or turn back?",
        "expect": ("turn", "creek", "slippery", "rainforest"),
    },
    {
        "region": "Moonee Beach",
        "question": "At Moonee Beach we found a sea snake or unknown marine animal on the sand. What should we do?",
        "expect": ("keep", "back", "snake", "000"),
    },
    {
        "region": "Coffs Harbour",
        "question": "A thunderstorm is building near the coast and we are on an exposed headland. What is the safest move?",
        "expect": ("lightning", "shelter", "exposed", "storm"),
    },
    {
        "region": "General Australia",
        "question": "Someone may have eaten a wild mushroom on a hike. What should we do?",
        "expect": ("13 11 26", "000", "mushroom", "do not"),
    },
    {
        "region": "General Australia",
        "question": "How do we treat a suspected snake bite while offline?",
        "expect": ("000", "still", "pressure", "immobilisation"),
    },
    {
        "region": "General Australia",
        "question": "I think a redback spider bit me at camp. Should I use a pressure bandage?",
        "expect": ("redback", "cold pack", "pressure", "13 11 26"),
    },
    {
        "region": "General Australia",
        "question": "What if the group is running out of water and one person wants to push on?",
        "expect": ("turn", "water", "group", "shade"),
    },
    {
        "region": "Flinders Ranges",
        "question": "How should we plan for heat on a remote Flinders Ranges walk?",
        "expect": ("heat", "water", "shade", "turn"),
    },
    {
        "region": "Kakadu",
        "question": "A crossing in Kakadu is flooded and there may be crocodiles. What should we do?",
        "expect": ("flood", "crocodile", "turn", "sign"),
    },
    {
        "region": "General Australia",
        "question": "We have no phone reception. What should have been done before leaving and what now?",
        "expect": ("plb", "satellite", "route", "battery"),
    },
    {
        "region": "Royal National Park",
        "question": "The cliffs are windy and someone wants a photo near the edge. What should I say?",
        "expect": ("cliff", "edge", "wind", "back"),
    },
    {
        "region": "General Australia",
        "question": "How do I decide when to turn around on a day walk?",
        "expect": ("turnaround", "weather", "water", "daylight"),
    },
    {
        "region": "General Australia",
        "question": "What are the top pre-walk checks before heading out of coverage?",
        "expect": ("weather", "route", "water", "plb"),
    },
]


def post_json(base_url: str, payload: dict, timeout: float) -> dict:
    request = Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def assess_answer(answer: str, expected_terms: tuple[str, ...]) -> dict:
    lower = answer.lower()
    found = [term for term in expected_terms if term.lower() in lower]
    missing = [term for term in expected_terms if term.lower() not in lower]
    return {"found": found, "missing": missing, "pass": len(found) >= max(2, len(expected_terms) - 1)}


def write_reports(results: list[dict], endpoint: str) -> None:
    OUT_JSON.write_text(json.dumps({"endpoint": endpoint, "results": results}, indent=2), encoding="utf-8")
    lines = [
        "# Survival Question Assessment",
        "",
        f"- Endpoint: `{endpoint}`",
        f"- Run at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Passed: `{sum(1 for item in results if item['assessment']['pass'])}/{len(results)}`",
        "",
        "| # | Region | Question | Backend | Risk | Assessment | Missing |",
        "|---:|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(results, 1):
        missing = ", ".join(item["assessment"]["missing"]) or "-"
        status = "pass" if item["assessment"]["pass"] else "review"
        lines.append(
            f"| {index} | {item['region']} | {item['question']} | {item['model_backend']} | "
            f"{item['risk_level']} | {status} | {missing} |"
        )
    lines.extend(["", "## Answer Notes", ""])
    for index, item in enumerate(results, 1):
        answer = item["answer"].replace("\n", " ")
        sources = " / ".join(source.get("matched_item", source.get("title", "")) for source in item.get("sources", []))
        lines.extend([f"### {index}. {item['question']}", "", answer, "", f"Sources: {sources or '-'}", ""])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--timeout", type=float, default=150)
    args = parser.parse_args()
    results = []
    for item in QUESTIONS:
        try:
            response = post_json(args.endpoint, {"message": item["question"], "region": item["region"]}, args.timeout)
            assessment = assess_answer(response.get("answer", ""), item["expect"])
            result = {
                "region": item["region"],
                "question": item["question"],
                "expected_terms": item["expect"],
                "model_backend": response.get("model_backend", ""),
                "risk_level": response.get("risk_level", ""),
                "answer": response.get("answer", ""),
                "sources": response.get("sources", []),
                "assessment": assessment,
            }
        except Exception as exc:
            result = {
                "region": item["region"],
                "question": item["question"],
                "expected_terms": item["expect"],
                "model_backend": "request_failed",
                "risk_level": "unknown",
                "answer": "",
                "sources": [],
                "assessment": {"found": [], "missing": list(item["expect"]), "pass": False, "error": str(exc)},
            }
        results.append(result)
        print(f"{len(results):02d}. {item['question']} -> {'pass' if result['assessment']['pass'] else 'review'}", flush=True)
        write_reports(results, args.endpoint)
    write_reports(results, args.endpoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
