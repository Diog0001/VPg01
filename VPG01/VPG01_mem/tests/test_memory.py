import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docx import Document

from documents.loaders import chunk_text, extract_text
from llm import build_history, generate_reply
from memory.brain import MemoryBrain
from memory.long_term import LongTermMemory, RetrievedChunk
from memory.sqlite_context import SQLiteContextStore


class SQLiteContextTests(unittest.TestCase):
    def test_stores_all_turns(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = Path(tmp) / "context.db"
            store = SQLiteContextStore(db_path=db_path)
            for index in range(15):
                store.append_turn(1, "user", f"сообщение {index}")

            turns = store.get_all_turns(1)
            self.assertEqual(len(turns), 15)
            self.assertEqual(turns[0].content, "сообщение 0")
            self.assertEqual(turns[-1].content, "сообщение 14")

    def test_persist_reloads_after_restart(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = Path(tmp) / "context.db"
            first = SQLiteContextStore(db_path=db_path)
            first.append_turn(3, "user", "Меня зовут Аня")
            first.append_turn(3, "assistant", "Приятно познакомиться")

            second = SQLiteContextStore(db_path=db_path)
            formatted = second.format_for_system_prompt(3)
            self.assertIn("Меня зовут Аня", formatted)
            self.assertIn("Приятно познакомиться", formatted)

            second.clear(3)
            third = SQLiteContextStore(db_path=db_path)
            self.assertEqual(third.turn_count(3), 0)

    def test_clear_drops_only_one_user(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = Path(tmp) / "context.db"
            store = SQLiteContextStore(db_path=db_path)
            store.append_turn(1, "user", "раз")
            store.append_turn(2, "user", "два")
            store.clear(1)
            self.assertEqual(store.turn_count(1), 0)
            self.assertEqual(store.turn_count(2), 1)


class DocumentLoaderTests(unittest.TestCase):
    def test_chunk_text_keeps_overlap(self) -> None:
        text = "А" * 400 + "\n\n" + "Б" * 400 + "\n\n" + "В" * 400
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(chunks[1].startswith(chunks[0][-50:]))

    def test_extract_txt(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            path = Path(tmp) / "note.txt"
            path.write_text("Офис в Казани", encoding="utf-8")
            self.assertIn("Казани", extract_text(path))

    def test_extract_docx(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            path = Path(tmp) / "note.docx"
            document = Document()
            document.add_paragraph("Цена Лапка-Про — 12400 рублей")
            document.save(path)
            self.assertIn("12400", extract_text(path))


class PromptTests(unittest.TestCase):
    def test_prompt_includes_persisted_context_and_rag(self) -> None:
        persisted = "Сохранённый контекст диалога (из базы данных):\nПользователь: Меня зовут Аня"
        retrieved = [RetrievedChunk("Офис на Баумана, 12", "sample.txt", 0.1)]
        messages = build_history(persisted, retrieved)

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Меня зовут Аня", messages[1]["content"])
        self.assertIn("Баумана", messages[2]["content"])
        self.assertTrue(all(item["role"] == "system" for item in messages))


class ChadApiTests(unittest.TestCase):
    def test_generate_reply_reads_response_field(self) -> None:
        from types import SimpleNamespace

        fake = SimpleNamespace(
            status_code=200,
            json=lambda: {"is_success": True, "response": "Офис на Баумана, 12"},
            text="{}",
        )
        with patch("llm._client") as client:
            client.return_value.post.return_value = fake
            reply = generate_reply(
                "",
                [RetrievedChunk("Офис на Баумана, 12", "sample.txt")],
                "Где офис?",
            )

        self.assertEqual(reply, "Офис на Баумана, 12")
        payload = client.return_value.post.call_args.kwargs["json"]
        self.assertEqual(payload["message"], "Где офис?")
        self.assertEqual(payload["history"][0]["role"], "system")


class LongTermMemoryTests(unittest.TestCase):
    def test_stores_and_retrieves_related_chunks(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            memory = LongTermMemory(persist_dir=Path(tmp))
            added = memory.add_chunks(
                42,
                "office.txt",
                [
                    "Офис КотоКорп находится в Казани, улица Баумана, дом 12.",
                    "Лапка-Про стоит 12400 рублей и умеет распознавать питомца.",
                ],
            )
            self.assertEqual(added, 2)

            hits = memory.query(42, "Какой адрес офиса?")
            self.assertTrue(hits)
            self.assertIn("Баумана", hits[0].text)
            self.assertEqual(hits[0].source, "office.txt")

            memory.clear(42)
            self.assertEqual(memory.chunk_count(42), 0)


class CombinedMemoryTests(unittest.TestCase):
    def test_brain_saves_file_and_dialogue(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            brain = MemoryBrain(chroma_dir=root / "chroma", db_path=root / "context.db")
            sample = root / "sample.txt"
            sample.write_text(
                "Офис КотоКорп: Казань, улица Баумана, дом 12.",
                encoding="utf-8",
            )
            chunks = brain.remember_file(7, sample, "sample.txt")
            self.assertGreaterEqual(chunks, 1)

            with patch("memory.brain.generate_reply", return_value="Офис на Баумана, 12") as mocked:
                reply = brain.answer(7, "Где офис?")

            self.assertEqual(reply, "Офис на Баумана, 12")
            persisted, retrieved, question = mocked.call_args.args
            self.assertEqual(question, "Где офис?")
            self.assertEqual(persisted, "")
            self.assertTrue(retrieved)
            self.assertEqual(brain.db.turn_count(7), 2)

    def test_save_dialog_indexes_sqlite_turns_in_chroma(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            brain = MemoryBrain(chroma_dir=root / "chroma", db_path=root / "context.db")
            brain.db.append_turn(8, "user", "Я из Казани")
            brain.db.append_turn(8, "assistant", "Запомнил")
            saved, indexed = brain.save_dialog(8)
            self.assertEqual(saved, 2)
            self.assertGreaterEqual(indexed, 1)

            restored = MemoryBrain(chroma_dir=root / "chroma", db_path=root / "context.db")
            self.assertIn("Казани", restored.db.format_for_system_prompt(8))
            hits = restored.long.query(8, "Откуда пользователь?")
            self.assertTrue(any("Казани" in hit.text for hit in hits))

    def test_clear_dialog_wipes_sqlite_only(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            brain = MemoryBrain(chroma_dir=root / "chroma", db_path=root / "context.db")
            brain.db.append_turn(9, "user", "тест")
            brain.clear_dialog(9)
            self.assertEqual(brain.db.turn_count(9), 0)


if __name__ == "__main__":
    unittest.main()
