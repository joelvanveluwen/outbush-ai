import unittest
from unittest.mock import patch
from io import BytesIO

from PIL import Image

from outbush_ai.core import (
    ask_outbush,
    build_checklist,
    danger_cards,
    encyclopedia_search,
    first_aid_flow,
    health_status,
    identify_photo,
    weather_advice,
)


class OutbushCoreTests(unittest.TestCase):
    def test_mushroom_answers_never_approve_eating(self):
        result = ask_outbush("Can I eat this wild mushroom?", "NSW")
        answer = result["answer"].lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("do not eat wild mushrooms", answer)
        self.assertNotIn("safe to eat", answer)
        self.assertTrue(result["sources"])

    def test_mushroom_guardrail_survives_llama_backend(self):
        with patch("outbush_ai.core.generate_with_llama", return_value="This looks interesting."):
            result = ask_outbush("Can I eat this wild mushroom?", "NSW")
        answer = result["answer"].lower()
        self.assertIn("do not eat wild mushrooms", answer)
        self.assertIn("foraging limit", answer)
        self.assertNotIn("safe to eat", answer)

    def test_photo_mushroom_is_critical(self):
        result = identify_photo(file_name="orange_mushroom.jpg", note="orange mushroom under gum tree")
        joined = " ".join(result["care_notes"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("do not eat wild mushrooms", joined)
        self.assertNotIn("safe to eat", joined)

    def test_photo_upload_is_analyzed_offline(self):
        image = Image.new("RGB", (640, 480), (70, 150, 80))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        result = identify_photo(
            file_name="field_photo.jpg",
            note="leafy track edge",
            image_bytes=buffer.getvalue(),
            content_type="image/jpeg",
        )
        self.assertEqual(result["model_backend"], "offline_image_heuristics")
        self.assertTrue(result["image_analysis"]["image_present"])
        self.assertEqual(result["image_analysis"]["dimensions"]["width"], 640)
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        self.assertIn("vegetation", labels)

    def test_webp_extension_does_not_trigger_spider_or_cloud(self):
        image = Image.new("RGB", (662, 463), (113, 105, 97))
        buffer = BytesIO()
        image.save(buffer, format="WEBP")
        result = identify_photo(
            file_name="images.webp",
            note="",
            image_bytes=buffer.getvalue(),
            content_type="image/webp",
        )
        candidate_text = " ".join(
            f"{candidate['label']} {candidate['confidence']} {candidate['reason']}"
            for candidate in result["candidates"]
        ).lower()
        notes = " ".join(result["care_notes"]).lower()
        self.assertNotIn("spider", candidate_text)
        self.assertNotIn("cloud", candidate_text)
        self.assertNotIn("spider bite", notes)
        self.assertEqual(result["risk_level"], "normal")
        self.assertIn("image-only species id unavailable", candidate_text)

    def test_snake_note_routes_photo_to_snake_flow(self):
        result = identify_photo(file_name="images.webp", note="snake on the track")
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        notes = " ".join(result["care_notes"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("snake", labels)
        self.assertIn("snake bite", notes)
        self.assertTrue(any("snake" in source["title"].lower() for source in result["sources"]))

    def test_vision_model_snake_result_routes_photo_to_snake_flow(self):
        image = Image.new("RGB", (662, 463), (113, 105, 97))
        buffer = BytesIO()
        image.save(buffer, format="WEBP")
        with patch(
            "outbush_ai.core.classify_with_vision_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "llama.cpp mtmd",
                "subject_type": "snake",
                "candidate_labels": ["brown snake-like reptile"],
                "confidence": "medium",
                "visual_evidence": "Long narrow body visible on the ground.",
                "field_guidance": "Keep distance.",
            },
        ):
            result = identify_photo(
                file_name="images.webp",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/webp",
            )
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        notes = " ".join(result["care_notes"]).lower()
        self.assertEqual(result["model_backend"], "llama.cpp mtmd")
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("snake", labels)
        self.assertIn("snake bite", notes)

    def test_snake_first_aid_escalates_to_000(self):
        result = first_aid_flow("snake bite on ankle")
        text = " ".join(result["steps"]).lower()
        self.assertIn("triple zero", text)
        self.assertIn("pressure immobilisation", text)

    def test_danger_cards_have_sources(self):
        cards = danger_cards()
        self.assertGreaterEqual(len(cards), 5)
        for card in cards:
            self.assertIn("source", card)
            self.assertIn("url", card["source"])

    def test_checklist_mentions_plb_and_live_conditions(self):
        checklist = build_checklist()
        text = checklist["export_text"].lower()
        self.assertIn("plb", text)
        self.assertIn("live bom forecast", text)
        self.assertIn("park status", text)
        self.assertIn("[ ]", checklist["export_text"])

    def test_encyclopedia_uses_packaged_sqlite(self):
        result = encyclopedia_search("Australian snakes", limit=3)
        self.assertEqual(result["knowledge"]["backend"], "sqlite")
        self.assertTrue(result["knowledge"]["fts_enabled"])
        self.assertGreaterEqual(result["knowledge"]["items"], 40)
        self.assertTrue(result["answer"])
        titles = [item["title"] for item in result["results"]]
        self.assertTrue(any("snake" in title.lower() for title in titles))
        self.assertTrue(result["results"][0]["source"]["url"].startswith("https://"))

    def test_weather_separates_climate_from_forecast(self):
        result = weather_advice("Blue Mountains", "dark anvil cloud")
        self.assertIn("not a live forecast", result["cloud_read"].lower() + " " + result["pre_trip_note"].lower())
        self.assertIn("bom", result["pre_trip_note"].lower())
        self.assertIn("weather_pack", result)

    def test_health_status(self):
        result = health_status()
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["offline_ready"])
        self.assertEqual(result["knowledge_backend"], "sqlite")
        self.assertGreaterEqual(result["knowledge_items"], 10)


if __name__ == "__main__":
    unittest.main()
