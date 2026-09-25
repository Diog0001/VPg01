import unittest

from vkbot.textutil import choice, safe_filename, split_text


class VkTextTests(unittest.TestCase):
    def test_choice(self) -> None:
        self.assertEqual(choice("Да"), "yes")
        self.assertEqual(choice("сохранить"), "yes")
        self.assertEqual(choice("Отмена"), "no")
        self.assertIsNone(choice("где офис"))

    def test_split_and_filename(self) -> None:
        parts = split_text("абвгд", 2)
        self.assertEqual(parts, ["аб", "вг", "д"])
        self.assertEqual(safe_filename(r"..\docs\office", "txt"), "office.txt")
        self.assertEqual(safe_filename("note.pdf", "pdf"), "note.pdf")


if __name__ == "__main__":
    unittest.main()
