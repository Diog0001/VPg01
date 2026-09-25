import unittest
from unittest.mock import patch

from memory.stateless import StatelessBrain


class StatelessBrainTests(unittest.TestCase):
    def test_answer_ignores_user_id(self) -> None:
        brain = StatelessBrain()
        with patch("memory.stateless.generate_stateless_reply", return_value="ok") as mocked:
            self.assertEqual(brain.answer(1, "Привет"), "ok")
            self.assertEqual(brain.answer(2, "Привет"), "ok")
            self.assertEqual(mocked.call_count, 2)
            mocked.assert_called_with("Привет")

    def test_separate_calls_do_not_share_state(self) -> None:
        brain = StatelessBrain()
        replies = ["Не знаю вашего имени.", "Не знаю вашего имени."]

        with patch("memory.stateless.generate_stateless_reply", side_effect=replies):
            first = brain.answer(1, "Меня зовут Аня")
            second = brain.answer(1, "Как меня зовут?")

        self.assertEqual(first, replies[0])
        self.assertEqual(second, replies[1])


class LlmHistoryTests(unittest.TestCase):
    def test_stateless_reply_uses_system_only(self) -> None:
        with patch("llm._call_chad", return_value="ответ") as mocked:
            from llm import generate_stateless_reply

            result = generate_stateless_reply("Вопрос")

        self.assertEqual(result, "ответ")
        history, message = mocked.call_args[0]
        self.assertEqual(message, "Вопрос")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "system")
        self.assertIn("без памяти", history[0]["content"].lower())
