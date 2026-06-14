import unittest
from collections import Counter

from modal_jobs.outbush_species_finetune import _training_targets


class TrainingTargetTests(unittest.TestCase):
    def test_modal_training_targets_cover_requested_categories(self):
        counts = Counter(item.get("category", item.get("subject_type")) for item in _training_targets())
        self.assertGreaterEqual(counts["snake"], 26)
        self.assertGreaterEqual(counts["spider"], 10)
        self.assertGreaterEqual(counts["marine"], 10)
        self.assertGreaterEqual(counts["plant"], 20)
        self.assertGreaterEqual(counts["bush_tucker"], 10)
        self.assertGreaterEqual(counts["mushroom"], 10)
        self.assertGreaterEqual(counts["cloud_weather"], 8)


if __name__ == "__main__":
    unittest.main()
