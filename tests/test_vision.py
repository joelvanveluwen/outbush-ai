import unittest
from types import SimpleNamespace
from unittest.mock import patch

from outbush_ai.vision import classify_with_vision_model


class VisionRuntimeTests(unittest.TestCase):
    def test_successful_vision_result_hides_raw_runtime_logs(self):
        completed = SimpleNamespace(
            returncode=0,
            stdout='{"subject_type":"snake","candidate_labels":["snake"],"confidence":"high","visual_evidence":"long body","field_guidance":"keep away"}',
            stderr="llama.cpp startup log",
        )
        with patch("outbush_ai.vision.vision_available", return_value=True), patch(
            "outbush_ai.vision.vision_status",
            return_value={"cli": "/tmp/llama-mtmd-cli", "model": "/tmp/model.gguf", "mmproj": "/tmp/mmproj.gguf"},
        ), patch("outbush_ai.vision.subprocess.run", return_value=completed):
            result = classify_with_vision_model(b"fake image", content_type="image/jpeg")

        self.assertTrue(result["ok"])
        self.assertEqual(result["subject_type"], "snake")
        self.assertEqual(result["model_backend"], "llama.cpp mtmd")
        self.assertNotIn("raw_text", result)


if __name__ == "__main__":
    unittest.main()
