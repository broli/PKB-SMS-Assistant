import unittest
import os
from modules import config_manager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_config.dat"
        config_manager.CONFIG_FILE = self.test_file
        config_manager._RUNTIME_OVERRIDES.clear()
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def tearDown(self):
        config_manager._RUNTIME_OVERRIDES.clear()
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_scramble_and_unscramble(self):
        original = '{"token": "xyz123"}'
        scrambled = config_manager.scramble(original)
        self.assertNotEqual(scrambled, original)
        restored = config_manager.unscramble(scrambled)
        self.assertEqual(restored, original)

    def test_save_and_load_config(self):
        test_data = {
            "access_token": "token123",
            "refresh_token": "refresh456",
            "goto_phone": "+19999999999"
        }
        self.assertTrue(config_manager.save_config(test_data))
        loaded = config_manager.load_config()
        self.assertEqual(loaded["access_token"], "token123")
        self.assertEqual(loaded["refresh_token"], "refresh456")
        self.assertEqual(loaded["goto_phone"], "+19999999999")

    def test_runtime_overrides(self):
        config_manager.set_runtime_override("gemini_api_key", "override_secret")
        loaded = config_manager.load_config()
        self.assertEqual(loaded["gemini_api_key"], "override_secret")

if __name__ == "__main__":
    unittest.main()

