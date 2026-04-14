import unittest
import os
import json
import time
from modules import rate_limiter

class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        # Override history file location to avoid affecting real data
        self.test_file = "test_history.json"
        rate_limiter.HISTORY_FILE = self.test_file
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_record_and_cooldown(self):
        self.assertEqual(rate_limiter.get_remaining_cooldown(), 0)
        
        rate_limiter.record_ai_call()
        cooldown = rate_limiter.get_remaining_cooldown()
        self.assertTrue(cooldown > 0)
        self.assertTrue(cooldown <= rate_limiter.COOLDOWN_SECONDS)
        
        # Test loading
        history = rate_limiter.load_history()
        self.assertIn("last_ai_call", history)

if __name__ == "__main__":
    unittest.main()
