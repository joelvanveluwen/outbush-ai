import unittest
from unittest.mock import patch
from io import BytesIO

from PIL import Image, ImageDraw

from outbush_ai.core import (
    ask_outbush,
    build_checklist,
    danger_cards,
    encyclopedia_search,
    first_aid_flow,
    health_status,
    identify_photo,
    random_knowledge,
    weather_advice,
    weather_locations,
)
from outbush_ai.content import KNOWLEDGE_ITEMS
from outbush_ai.weather import resolve_region


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

    def test_redback_danger_question_prioritises_redback_guidance(self):
        with patch("outbush_ai.core.llama_available", return_value=True), patch(
            "outbush_ai.core.generate_with_llama",
            return_value=(
                "Yes. Redback spiders are dangerous. Keep distance, do not handle them, "
                "wash a bite, use a cold pack, and get medical advice if pain is severe."
            ),
        ):
            result = ask_outbush("Is a red back spider dangerous?", "NSW")
        answer = result["answer"].lower()
        matched_items = [source["matched_item"].lower() for source in result["sources"]]
        joined_sources = " ".join(matched_items)
        self.assertEqual(result["risk_level"], "high")
        self.assertEqual(result["model_backend"], "llama.cpp")
        self.assertIn("yes", answer)
        self.assertIn("redback", answer)
        self.assertIn("cold pack", answer)
        self.assertIn("redback spider", joined_sources)
        self.assertIn("redback spider first aid", joined_sources)
        self.assertNotIn("cassowary", joined_sources)
        self.assertNotIn("dingo", joined_sources)
        self.assertNotIn("red-bellied black snake", joined_sources)

    def test_chat_prefers_llama_answer_over_deterministic_safety_prose(self):
        with patch("outbush_ai.core.llama_available", return_value=True), patch(
            "outbush_ai.core.generate_with_llama",
            return_value="Model answer: keep clear and use redback bite first aid if bitten.",
        ):
            result = ask_outbush("Is a redback spider dangerous?", "NSW")
        answer = result["answer"].lower()
        self.assertEqual(result["risk_level"], "high")
        self.assertIn("model answer", answer)
        self.assertIn("redback bite first aid", answer)
        self.assertNotIn("relevant offline notes", answer)

    def test_chat_cleans_model_think_markers(self):
        with patch("outbush_ai.core.llama_available", return_value=True), patch(
            "outbush_ai.core.generate_with_llama",
            return_value="Answer: Call 13 11 26 and keep the person calm. </think> duplicate fragment",
        ):
            result = ask_outbush("Someone may have eaten a wild mushroom.", "NSW")
        answer = result["answer"].lower()
        self.assertIn("call 13 11 26", answer)
        self.assertNotIn("think", answer)
        self.assertNotIn("duplicate fragment", answer)

    def test_redback_pressure_bandage_answer_is_safety_corrected(self):
        with patch("outbush_ai.core.llama_available", return_value=True), patch(
            "outbush_ai.core.generate_with_llama",
            return_value=(
                "Yes, use a pressure bandage. Redback bites are not treated with pressure immobilisation."
            ),
        ):
            result = ask_outbush("I think a redback spider bit me at camp. Should I use a pressure bandage?", "NSW")
        answer = result["answer"].lower()
        self.assertIn("no. do not use pressure immobilisation", answer)
        self.assertIn("cold pack", answer)
        self.assertNotIn("yes, use a pressure bandage", answer)

    def test_rising_creek_answer_is_safety_corrected(self):
        with patch("outbush_ai.core.llama_available", return_value=True), patch(
            "outbush_ai.core.generate_with_llama",
            return_value="Yes, keep going. The creek is rising but the track is probably fine.",
        ):
            result = ask_outbush("Rainforest creek is rising near Dorrigo. Keep going or turn back?", "Dorrigo")
        answer = result["answer"].lower()
        self.assertIn("turn back", answer)
        self.assertIn("do not continue", answer)
        self.assertNotIn("yes, keep going", answer)

    def test_cliff_edge_photo_answer_is_safety_corrected(self):
        with patch("outbush_ai.core.llama_available", return_value=True), patch(
            "outbush_ai.core.generate_with_llama",
            return_value="If the weather is clear, it is safe to go ahead and take a photo near the edge.",
        ):
            result = ask_outbush("The cliffs are windy and someone wants a photo near the edge. What should I say?", "NSW")
        answer = result["answer"].lower()
        self.assertIn("say no", answer)
        self.assertIn("step back", answer)
        self.assertNotIn("safe to go ahead", answer)

    def test_no_reception_pre_walk_uses_bushwalking_sources(self):
        with patch("outbush_ai.core.generate_with_llama", return_value=None):
            result = ask_outbush("What are the top pre-walk checks before heading out of coverage?", "NSW")
        matched = " ".join(source["matched_item"].lower() for source in result["sources"])
        answer = result["answer"].lower()
        self.assertIn("bushwalking preparation", matched)
        self.assertNotIn("redback spider", matched)
        self.assertIn("pre-walk field anchor", answer)

    def test_chat_does_not_fabricate_deterministic_answer_without_model(self):
        result = ask_outbush("How do I cross a flooded creek?", "NSW")
        answer = result["answer"].lower()
        self.assertEqual(result["model_backend"], "text_model_unavailable")
        self.assertIn("local text model unavailable", answer)
        self.assertNotIn("most relevant offline notes", answer)

    def test_foraging_footer_uses_whole_words(self):
        with patch("outbush_ai.core.generate_with_llama", return_value=None):
            result = ask_outbush("How do we treat a suspected snake bite while offline?", "NSW")
        answer = result["answer"].lower()
        self.assertIn("snake-bite field anchor", answer)
        self.assertNotIn("foraging limit", answer)

    def test_cliff_edge_photo_question_gets_specific_guardrail(self):
        with patch("outbush_ai.core.generate_with_llama", return_value=None):
            result = ask_outbush("The cliffs are windy and someone wants a photo near the edge. What should I say?", "NSW")
        answer = result["answer"].lower()
        self.assertEqual(result["risk_level"], "high")
        self.assertIn("cliff-edge field anchor", answer)
        self.assertIn("step back", answer)

    def test_unavailable_model_keeps_key_field_anchors(self):
        cases = {
            "What should I pack before walking to Kosciuszko in cold windy weather?": (
                "alpine field anchor",
                "warm waterproof",
                "turnaround",
            ),
            "At Moonee Beach we found a sea snake on the sand. What should we do?": (
                "marine animal field anchor",
                "keep back",
                "snake",
            ),
            "A crossing in Kakadu is flooded and there may be crocodiles. What should we do?": (
                "crocodile field anchor",
                "warning signs",
                "turn back",
            ),
        }
        with patch("outbush_ai.core.generate_with_llama", return_value=None):
            for question, expected_terms in cases.items():
                with self.subTest(question=question):
                    answer = ask_outbush(question, "General Australia")["answer"].lower()
                    for term in expected_terms:
                        self.assertIn(term, answer)

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

    def test_named_dangerous_snake_notes_route_to_snake_flow(self):
        result = identify_photo(file_name="beach.jpg", note="yellow bellied sea snake on the sand")
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        notes = " ".join(result["care_notes"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("snake", labels)
        self.assertIn("snake bite", notes)

    def test_species_model_result_routes_photo_to_candidate_hint(self):
        image = Image.new("RGB", (662, 463), (113, 105, 97))
        buffer = BytesIO()
        image.save(buffer, format="WEBP")
        with patch(
            "outbush_ai.core.classify_with_species_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "outbush field-tuned species classifier",
                "subject_type": "snake",
                "candidate_labels": ["yellow-bellied sea snake"],
                "confidence": "medium",
                "score": 0.91,
                "risk": "critical",
                "visual_evidence": "Compared against licensed examples.",
                "field_guidance": "Keep people and dogs back from the animal.",
                "source": {"title": "Training manifest", "url": "https://example.com/model"},
            },
        ):
            result = identify_photo(
                file_name="images.webp",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/webp",
            )
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        self.assertIn("field-tuned candidate", labels)
        self.assertIn("yellow-bellied sea snake", labels)
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("outbush field-tuned species classifier", result["model_backend"])

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

    def test_red_bellied_vision_label_is_downgraded_without_colour_cue(self):
        image = Image.new("RGB", (640, 900), (85, 120, 70))
        draw = ImageDraw.Draw(image)
        draw.rectangle((240, 40, 320, 860), fill=(70, 74, 56))
        draw.line([(110, 800), (180, 650), (260, 470), (345, 310), (455, 210)], fill=(68, 70, 52), width=52)
        for x, y in [(150, 730), (225, 570), (300, 410), (392, 255)]:
            draw.ellipse((x - 24, y - 12, x + 24, y + 12), fill=(190, 184, 122))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        with patch("outbush_ai.core.classify_with_species_model", return_value=None), patch(
            "outbush_ai.core.classify_with_vision_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "llama.cpp mtmd",
                "subject_type": "snake",
                "candidate_labels": ["red-bellied black snake", "western brown snake"],
                "confidence": "medium",
                "visual_evidence": "a snake is coiled on tree trunks with visible patterned skin",
                "field_guidance": "keep distance",
            },
        ):
            result = identify_photo(
                file_name="patterned-python-like-snake.png",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/png",
            )
        candidate_text = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("patterned snake or python-like animal", candidate_text)
        self.assertNotIn("red-bellied black snake", candidate_text)
        self.assertEqual(result["vision_model"]["guardrail"], "red_bellied_colour_cue_absent")
        self.assertIn("red-bellied black snake", " ".join(result["vision_model"]["original_candidate_labels"]).lower())

    def test_red_bellied_species_label_is_downgraded_without_colour_cue(self):
        image = Image.new("RGB", (640, 900), (80, 125, 75))
        draw = ImageDraw.Draw(image)
        draw.line([(120, 810), (210, 640), (320, 480), (410, 300), (500, 180)], fill=(65, 70, 54), width=54)
        for x, y in [(165, 740), (250, 600), (350, 430), (445, 250)]:
            draw.ellipse((x - 28, y - 14, x + 28, y + 14), fill=(194, 186, 126))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        with patch(
            "outbush_ai.core.classify_with_species_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "outbush field-tuned species classifier",
                "subject_type": "snake",
                "candidate_labels": ["red-bellied black snake"],
                "confidence": "high",
                "score": 0.98,
                "score_margin": 0.08,
                "risk": "critical",
                "visual_evidence": "Compared against licensed examples.",
                "field_guidance": "Keep distance.",
            },
        ), patch("outbush_ai.core.classify_with_vision_model", return_value=None):
            result = identify_photo(
                file_name="tree-python-like-snake.png",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/png",
            )
        candidate_text = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("snake or snake-like animal", candidate_text)
        self.assertNotIn("red-bellied black snake", candidate_text)
        self.assertEqual(result["species_model"]["guardrail"], "red_bellied_colour_cue_absent")
        self.assertIn("outbush field-tuned species classifier", result["model_backend"])

    def test_low_confidence_vision_conflict_does_not_escalate_field_kit(self):
        image = Image.new("RGB", (662, 463), (113, 105, 97))
        buffer = BytesIO()
        image.save(buffer, format="WEBP")
        with patch(
            "outbush_ai.core.classify_with_species_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "outbush field-tuned species classifier",
                "subject_type": "snake",
                "candidate_labels": ["tiger snake"],
                "confidence": "low",
                "score": 0.96,
                "score_margin": 0.002,
                "risk": "critical",
            },
        ), patch(
            "outbush_ai.core.classify_with_vision_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "llama.cpp mtmd",
                "subject_type": "snake",
                "candidate_labels": ["snake"],
                "confidence": "high",
                "visual_evidence": "snake on backpack",
                "field_guidance": "keep away",
            },
        ):
            result = identify_photo(
                file_name="field_kit.webp",
                note="Raspberry Pi field kit on backpack, no animal visible",
                image_bytes=buffer.getvalue(),
                content_type="image/webp",
            )
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        self.assertEqual(result["risk_level"], "normal")
        self.assertNotIn("snake bite", " ".join(result["care_notes"]).lower())
        self.assertIn("uploaded field photo", labels)

    def test_low_confidence_species_snake_hint_still_surfaces_hazard(self):
        image = Image.new("RGB", (1024, 768), (128, 129, 109))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        with patch(
            "outbush_ai.core.classify_with_species_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "outbush field-tuned species classifier",
                "subject_type": "snake",
                "candidate_labels": ["highlands copperhead"],
                "confidence": "low",
                "score": 0.9839,
                "score_margin": 0.0002,
                "top_matches": [
                    {"label": "highlands copperhead", "score": 0.9839, "risk": "critical"},
                    {"label": "eastern brown snake", "score": 0.9837, "risk": "critical"},
                ],
                "risk": "critical",
                "hazard_group": "snake",
                "field_guidance": "Keep distance and use snake-bite first aid for any suspected bite.",
            },
        ), patch(
            "outbush_ai.core.classify_with_vision_model",
            return_value={
                "available": True,
                "ok": False,
                "error": "vision model returned no parseable JSON",
                "model_backend": "llama.cpp mtmd",
            },
        ):
            result = identify_photo(
                file_name="large.jpeg",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/jpeg",
        )
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        candidate_text = " ".join(
            f"{candidate['label']} {candidate['confidence']} {candidate['reason']}"
            for candidate in result["candidates"]
        ).lower()
        notes = " ".join(result["care_notes"]).lower()
        sources = " ".join(source.get("title", "") for source in result["sources"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("possible snake or snake-like animal", labels)
        self.assertIn("species scores were too close", candidate_text)
        self.assertIn("snake bite", notes)
        self.assertIn("snake bites", sources)
        self.assertIn("outbush field-tuned species classifier", result["model_backend"])

    def test_red_bellied_colour_cue_supports_snake_candidate(self):
        image = Image.new("RGB", (640, 360), (45, 45, 40))
        draw = ImageDraw.Draw(image)
        draw.rectangle((100, 160, 550, 230), fill=(15, 18, 16))
        draw.rectangle((120, 218, 520, 255), fill=(165, 45, 30))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        with patch("outbush_ai.core.classify_with_species_model", return_value=None), patch(
            "outbush_ai.core.classify_with_vision_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "llama.cpp mtmd",
                "subject_type": "snake",
                "candidate_labels": ["snake"],
                "confidence": "medium",
                "visual_evidence": "long dark snake-like body",
                "field_guidance": "keep away",
            },
        ):
            result = identify_photo(
                file_name="snake.jpg",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/jpeg",
            )
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("red-bellied black snake", labels)
        self.assertTrue(result["image_analysis"]["red_bellied_black_snake_cue"]["cue"])

    def test_warm_brown_snake_colours_do_not_trigger_red_bellied_cue(self):
        image = Image.new("RGB", (640, 360), (155, 78, 48))
        draw = ImageDraw.Draw(image)
        draw.line([(80, 120), (200, 90), (340, 145), (500, 115)], fill=(45, 42, 34), width=44)
        draw.line([(100, 160), (260, 195), (420, 175), (560, 205)], fill=(120, 70, 45), width=36)
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        with patch("outbush_ai.core.classify_with_species_model", return_value=None), patch(
            "outbush_ai.core.classify_with_vision_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "llama.cpp mtmd",
                "subject_type": "snake",
                "candidate_labels": ["brown snake"],
                "confidence": "medium",
                "visual_evidence": "brown snake-like body",
                "field_guidance": "keep away",
            },
        ):
            result = identify_photo(
                file_name="brown-snake.jpg",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/jpeg",
            )
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        self.assertFalse(result["image_analysis"]["red_bellied_black_snake_cue"]["cue"])
        self.assertNotIn("red-bellied black snake", labels)

    def test_red_bellied_colour_cue_uses_low_confidence_snake_top_match(self):
        image = Image.new("RGB", (640, 360), (120, 120, 110))
        draw = ImageDraw.Draw(image)
        draw.rectangle((90, 145, 560, 225), fill=(16, 21, 20))
        draw.rectangle((115, 214, 530, 260), fill=(175, 50, 32))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        with patch(
            "outbush_ai.core.classify_with_species_model",
            return_value={
                "available": True,
                "ok": True,
                "model_backend": "outbush field-tuned species classifier",
                "subject_type": "animal",
                "candidate_labels": ["saltwater crocodile"],
                "confidence": "low",
                "top_matches": [
                    {"label": "saltwater crocodile", "score": 0.97, "risk": "critical"},
                    {"label": "tiger snake", "score": 0.96, "risk": "critical"},
                ],
            },
        ), patch("outbush_ai.core.classify_with_vision_model", return_value=None):
            result = identify_photo(
                file_name="uploaded-image.png",
                note="",
                image_bytes=buffer.getvalue(),
                content_type="image/png",
            )
        labels = " ".join(candidate["label"] for candidate in result["candidates"]).lower()
        source_titles = " ".join(source["title"] for source in result["sources"]).lower()
        self.assertEqual(result["risk_level"], "critical")
        self.assertIn("red-bellied black snake", labels)
        self.assertIn("snake bites", source_titles)

    def test_snake_first_aid_escalates_to_000(self):
        result = first_aid_flow("snake bite on ankle")
        text = " ".join(result["steps"]).lower()
        self.assertIn("triple zero", text)
        self.assertIn("pressure immobilisation", text)

    def test_redback_first_aid_differs_from_funnel_web(self):
        result = first_aid_flow("redback bite cold pack 13 11 26")
        text = " ".join(result["steps"]).lower()
        self.assertIn("cold pack", text)
        self.assertIn("13 11 26", text)
        self.assertIn("do not use pressure immobilisation", text)

    def test_danger_cards_have_sources(self):
        cards = danger_cards()
        self.assertGreaterEqual(len(cards), 8)
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
        self.assertGreaterEqual(result["knowledge"]["items"], 60)
        self.assertTrue(result["answer"])
        titles = [item["title"] for item in result["results"]]
        self.assertTrue(any("snake" in title.lower() for title in titles))
        self.assertTrue(result["results"][0]["source"]["url"].startswith("https://"))

    def test_encyclopedia_retrieves_requested_dangerous_animals(self):
        cases = {
            "yellow bellied sea snake beach": "yellow-bellied sea snake",
            "red belly black snake creek": "red-bellied black snake",
            "funnel web spider shoe": "funnel-web",
            "redback spider bite cold pack": "redback",
            "stonefish reef footwear": "stonefish",
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                result = encyclopedia_search(query, limit=4)
                joined_titles = " ".join(item["title"].lower() for item in result["results"])
                self.assertIn(expected, joined_titles)

    def test_expanded_rag_pack_has_required_scale_and_topics(self):
        self.assertGreaterEqual(len(KNOWLEDGE_ITEMS), 325)
        self.assertLessEqual(len(KNOWLEDGE_ITEMS), 650)
        self.assertGreaterEqual(sum(1 for item in KNOWLEDGE_ITEMS if "top 50 parks" in item.tags), 150)
        titles = " ".join(item.title.lower() for item in KNOWLEDGE_ITEMS)
        self.assertIn("witchetty grub", titles)
        self.assertIn("ranger tip", titles)
        self.assertIn("uluru-kata tjuta", titles)

    def test_random_knowledge_returns_one_local_item(self):
        result = random_knowledge()
        self.assertEqual(result["mode"], "encyclopedia_random")
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("answer", result)

    def test_weather_separates_climate_from_forecast(self):
        result = weather_advice("Blue Mountains", "dark anvil cloud")
        self.assertIn("not a live forecast", result["cloud_read"].lower() + " " + result["pre_trip_note"].lower())
        self.assertIn("bom", result["pre_trip_note"].lower())
        self.assertIn("weather_pack", result)

    def test_weather_locations_cover_common_demo_regions(self):
        data = weather_locations()
        names = " ".join(location["name"].lower() for location in data["locations"])
        self.assertGreaterEqual(data["count"], 100)
        for expected in ("moonee beach", "coffs harbour", "dorrigo", "kosciuszko"):
            self.assertIn(expected, names)
        self.assertEqual(resolve_region("Kosciusko")["matched"], "Kosciuszko National Park")
        self.assertEqual(resolve_region("Moonee Beach")["matched"], "Moonee Beach")
        self.assertEqual(resolve_region("Dorrigo")["matched"], "Dorrigo")

    def test_survival_queries_pin_relevant_rag_sources(self):
        cases = {
            "How do I cross a flooded creek?": "Floodwater and creek turnback",
            "We lost the track and have no phone reception. What now?": "Lost or misplaced track flow",
            "Thunderstorm building on an exposed headland. What now?": "Lightning and exposed-ground shelter",
            "How do I decide when to turn around on a day walk?": "Group turnaround decision",
            "What should I pack for Kosciuszko cold windy weather?": "Kosciuszko alpine conditions",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                result = ask_outbush(question, "General Australia")
                matched = " ".join(source["matched_item"] for source in result["sources"]).lower()
                self.assertIn(expected.lower(), matched)

    def test_health_status(self):
        result = health_status()
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["offline_ready"])
        self.assertEqual(result["knowledge_backend"], "sqlite")
        self.assertGreaterEqual(result["knowledge_items"], 10)
        self.assertIn("text_model", result)
        self.assertIn("auto_setup", result["text_model"])
        self.assertIn("species_model_configured", result)
        self.assertIn("species_model_labels", result)


if __name__ == "__main__":
    unittest.main()
