from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from config import CONTEXT_DB, CONTEXT_PROMPT_MAX_CHARS


@dataclass(frozen=True)
class StoredTurn:
    role: str
    content: str


class SQLiteContextStore:
    """Полная история диалога в SQLite (без обрезки при сохранении)."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or CONTEXT_DB
        self._lock = Lock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def warmup(self) -> tuple[int, int]:
        with self._lock:
            users = self._conn().execute(
                "SELECT COUNT(DISTINCT user_id) FROM turns"
            ).fetchone()[0]
            turns = self._conn().execute("SELECT COUNT(*) FROM turns").fetchone()[0]
        return int(users or 0), int(turns or 0)

    def append_turn(self, user_id: int, role: str, content: str) -> None:
        text = content.strip()
        if role not in {"user", "assistant"} or not text:
            return
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._conn()
            conn.execute(
                "INSERT INTO turns(user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (user_id, role, text, now),
            )
            conn.commit()

    def get_all_turns(self, user_id: int) -> list[StoredTurn]:
        with self._lock:
            rows = self._conn().execute(
                """
                SELECT role, content FROM turns
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()
        return [StoredTurn(role=str(role), content=str(content)) for role, content in rows]

    def turn_count(self, user_id: int) -> int:
        with self._lock:
            row = self._conn().execute(
                "SELECT COUNT(*) FROM turns WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return int(row[0] if row else 0)

    def clear(self, user_id: int) -> None:
        with self._lock:
            conn = self._conn()
            conn.execute("DELETE FROM turns WHERE user_id = ?", (user_id,))
            conn.commit()

    def format_for_system_prompt(
        self,
        user_id: int,
        max_chars: int = CONTEXT_PROMPT_MAX_CHARS,
    ) -> str:
        turns = self.get_all_turns(user_id)
        if not turns:
            return ""

        lines = ["Сохранённый контекст диалога (из базы данных):"]
        for turn in turns:
            who = "Пользователь" if turn.role == "user" else "Бот"
            lines.append(f"{who}: {turn.content}")
        body = "\n".join(lines)

        if max_chars > 0 and len(body) > max_chars:
            omitted = len(body) - max_chars
            body = (
                "Сохранённый контекст диалога (из базы данных).\n"
                f"Внимание: для лимита модели показаны только последние ~{max_chars} символов; "
                f"в SQLite по-прежнему хранятся все {len(turns)} реплик.\n\n"
                + body[-max_chars:]
            )
        return body

    def _init_schema(self) -> None:
        with self._lock:
            conn = self._conn()
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_user_id ON turns(user_id, id)"
            )
            conn.commit()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
