import unittest
import os
from modules import contact_book

class TestContactBook(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_contacts.json"
        contact_book.CONTACTS_FILE = self.test_file
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_clean_phone(self):
        self.assertEqual(contact_book._clean_phone("1234567890"), "+11234567890")
        self.assertEqual(contact_book._clean_phone("(123) 456-7890"), "+11234567890")
        self.assertEqual(contact_book._clean_phone("+11234567890"), "+11234567890")
        self.assertEqual(contact_book._clean_phone("123"), "")

    def test_save_and_load_contacts(self):
        data = {
            "+11234567890": {"name": "Alice Smith", "nickname": "Alice"}
        }
        self.assertTrue(contact_book.save_contacts(data))
        loaded = contact_book.load_contacts()
        self.assertEqual(loaded, data)

    def test_get_display_name(self):
        db = {
            "+11111111111": {"name": "Bob Official", "nickname": "Bobby"},
            "+12222222222": {"name": "Charlie", "nickname": ""},
            "+13333333333": {"name": "", "nickname": ""},
        }
        self.assertEqual(contact_book.get_display_name("+11111111111", db), "Bobby")
        self.assertEqual(contact_book.get_display_name("+12222222222", db), "Charlie")
        self.assertEqual(contact_book.get_display_name("+13333333333", db), "+13333333333")
        self.assertEqual(contact_book.get_display_name("+19999999999", db), "+19999999999")

    def test_set_nickname(self):
        db = {}
        updated = contact_book.set_nickname("+11111111111", "My Friend", db)
        self.assertIn("+11111111111", updated)
        self.assertEqual(updated["+11111111111"]["nickname"], "My Friend")

if __name__ == "__main__":
    unittest.main()
