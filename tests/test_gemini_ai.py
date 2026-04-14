import unittest
from unittest.mock import patch, MagicMock
from modules import gemini_ai

class TestGeminiAI(unittest.TestCase):
    @patch('modules.gemini_ai.genai.Client')
    def test_generate_reply_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Hello, client!"
        mock_client.models.generate_content.return_value = mock_response

        reply = gemini_ai.generate_reply("fake_key", "chat history", "Professional", "greet")
        self.assertEqual(reply, "Hello, client!")
        mock_client.models.generate_content.assert_called_once()

    def test_generate_reply_no_key(self):
        reply = gemini_ai.generate_reply("", "history", "tone", "intent")
        self.assertTrue(reply.startswith("Error:"))

if __name__ == "__main__":
    unittest.main()
