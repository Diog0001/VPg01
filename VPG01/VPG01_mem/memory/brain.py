from pathlib import Path

from config import CONTEXT_DB
from documents.loaders import chunk_text, extract_text
from llm import generate_reply
from memory.long_term import LongTermMemory
from memory.sqlite_context import SQLiteContextStore

SAVED_DIALOG_SOURCE = "сохранённый_диалог"


class MemoryBrain:
    """Полная история в SQLite + ChromaDB для документов."""

    def __init__(
        self,
        chroma_dir: Path | None = None,
        db_path: Path | None = None,
    ) -> None:
        self.db = SQLiteContextStore(db_path=db_path or CONTEXT_DB)
        self.long = LongTermMemory(persist_dir=chroma_dir)

    def warmup(self) -> tuple[int, int]:
        return self.db.warmup()

    def remember_file(self, user_id: int, path: Path, filename: str) -> int:
        text = extract_text(path)
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("В файле не нашлось текста, который можно сохранить.")
        return self.long.add_chunks(user_id, filename, chunks)

    def save_dialog(self, user_id: int) -> tuple[int, int]:
        """Дублирует весь диалог из SQLite в векторную базу для семантического поиска."""
        turns = self.db.get_all_turns(user_id)
        if not turns:
            return 0, 0

        lines = ["Сохранённый диалог с пользователем."]
        for turn in turns:
            who = "Пользователь" if turn.role == "user" else "Бот"
            lines.append(f"{who}: {turn.content}")
        chunks = chunk_text("\n\n".join(lines))
        indexed = self.long.replace_chunks(user_id, SAVED_DIALOG_SOURCE, chunks)
        return len(turns), indexed

    def answer(self, user_id: int, question: str) -> str:
        persisted = self.db.format_for_system_prompt(user_id)
        retrieved = self.long.query(user_id, question)
        reply = generate_reply(persisted, retrieved, question)
        self.db.append_turn(user_id, "user", question)
        self.db.append_turn(user_id, "assistant", reply)
        return reply

    def clear_dialog(self, user_id: int) -> None:
        self.db.clear(user_id)

    def status(self, user_id: int) -> str:
        sources = self.long.list_sources(user_id)
        docs = ", ".join(sources) if sources else "нет"
        return (
            f"Контекст в SQLite: {self.db.turn_count(user_id)} реплик (все сохраняются).\n"
            f"Долгая память: {self.long.chunk_count(user_id)} фрагментов.\n"
            f"Документы: {docs}"
        )
