from functools import lru_cache

import httpx

from config import CHAD_API_BASE, CHAD_API_KEY, CHAD_MODEL
from memory.long_term import RetrievedChunk

SYSTEM_PROMPT = """Ты Telegram-бот с долговременной памятью.

У тебя два источника контекста:
1) Сохранённый диалог — блок «Сохранённый контекст диалога» из базы данных SQLite.
2) Долгая память — фрагменты документов из векторной базы ChromaDB.

Правила:
- Если вопрос про содержимое документов, опирайся на найденные фрагменты и называй файл-источник.
- Если фрагменты нерелевантны или их нет, опирайся на сохранённый диалог и текущий вопрос.
- Не выдумывай факты «из документа», которых нет во фрагментах.
- Если информации недостаточно, так и скажи.
- Отвечай на языке пользователя, кратко и по делу.
"""


@lru_cache(maxsize=1)
def _client() -> httpx.Client:
    return httpx.Client(timeout=90.0)


def build_history(
    persisted_context: str,
    retrieved: list[RetrievedChunk],
) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if persisted_context.strip():
        messages.append({"role": "system", "content": persisted_context.strip()})
    else:
        messages.append(
            {
                "role": "system",
                "content": "В SQLite пока нет сохранённого контекста диалога для этого пользователя.",
            }
        )

    if retrieved:
        context_parts = []
        for index, chunk in enumerate(retrieved, start=1):
            context_parts.append(
                f"[{index}] Источник: {chunk.source}\n{chunk.text}"
            )
        messages.append(
            {
                "role": "system",
                "content": "Фрагменты из долгой памяти:\n\n"
                + "\n\n---\n\n".join(context_parts),
            }
        )
    else:
        messages.append(
            {
                "role": "system",
                "content": "В долгой памяти пока нет релевантных фрагментов по этому вопросу.",
            }
        )

    return messages


def generate_reply(
    persisted_context: str,
    retrieved: list[RetrievedChunk],
    question: str,
) -> str:
    url = f"{CHAD_API_BASE.rstrip('/')}/{CHAD_MODEL}"
    payload = {
        "api_key": CHAD_API_KEY,
        "message": question,
        "history": build_history(persisted_context, retrieved),
        "temperature": 0.3,
    }

    try:
        response = _client().post(url, json=payload)
    except httpx.HTTPError as error:
        raise RuntimeError(f"Не удалось связаться с ChadGPT: {error}") from error

    if response.status_code != 200:
        raise RuntimeError(
            f"ChadGPT вернул HTTP {response.status_code}: {response.text[:400]}"
        )

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError("ChadGPT вернул не JSON.") from error

    if not data.get("is_success"):
        code = data.get("error_code") or "ошибка"
        message = data.get("error_message") or "неизвестная ошибка ChadGPT"
        raise RuntimeError(f"ChadGPT [{code}]: {message}")

    return str(data.get("response") or "").strip()
