import unittest
from datetime import date, datetime, timedelta

import ai_digest
import self_development


class AiDigestContractTest(unittest.TestCase):
    def test_vetted_fallback_keeps_exactly_six_linked_items(self):
        digest = ai_digest.build_proven_digest(datetime(2026, 10, 11), [])
        self.assertTrue(ai_digest.is_deliverable_digest(digest))
        self.assertTrue(ai_digest.has_complete_editorial_contract(digest))
        self.assertEqual(len(ai_digest.digest_links(digest)), 6)

    def test_editorial_contract_rejects_missing_section(self):
        digest = ai_digest.build_proven_digest(datetime(2026, 10, 11), [])
        broken = digest.replace("🛠 <b>Скиллы для своей LLM</b>", "")
        self.assertFalse(ai_digest.has_complete_editorial_contract(broken))


class SelfDevelopmentDeliveryTest(unittest.TestCase):
    def test_same_day_history_blocks_duplicate_delivery(self):
        today = date(2026, 10, 12)
        self.assertTrue(self_development.delivered_for_date([{"date": today.isoformat()}], today))
        self.assertFalse(
            self_development.delivered_for_date([{"date": (today - timedelta(days=1)).isoformat()}], today)
        )

    def test_daily_sprint_advances_by_weekday(self):
        monday = date(2026, 10, 12)
        _, monday_session = self_development.choose_daily_session(monday)
        _, tuesday_session = self_development.choose_daily_session(monday + timedelta(days=1))
        self.assertNotEqual(monday_session["title"], tuesday_session["title"])


if __name__ == "__main__":
    unittest.main()
