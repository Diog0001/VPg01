from functools import lru_cache

import httpx

from config import CHAD_API_BASE, CHAD_API_KEY, CHAD_MODEL

SYSTEM_PROMPT = """Ты Telegram-бот без памяти между сообщениями.

Правила:
- У тебя нет доступа к прошлым репликам диалога.
- Отвечай только на текущий вопрос пользователя.
- Если пользователь ссылается на то, что «говорил раньше», честно скажи, что ты этого не помнишь.
- Отвечай на языке пользователя, кратко и по делу.
"""

DOCUMENT_SYSTEM_PROMPT = """Ты Telegram-бот без памяти. Пользователь прислал файл один раз.
Дай краткое содержание документа и 3–5 ключевых фактов из текста.
Не выдумывай то, чего нет в переданном фрагменте.
Если текст обрезан, упомяни, что видишь только начало файла.
"""

MAX_DOCUMENT_CHARS = 12000


@lru_cache(maxsize=1)
def _client() -> httpx.Client:
    return httpx.Client(timeout=90.0)


def _call_chad(history: list[dict[str, str]], message: str) -> str:
    url = f"{CHAD_API_BASE.rstrip('/')}/{CHAD_MODEL}"
    payload = {
        "api_key": CHAD_API_KEY,
        "message": message,
        "history": history,
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
        err_message = data.get("error_message") or "неизвестная ошибка ChadGPT"
        raise RuntimeError(f"ChadGPT [{code}]: {err_message}")

    return str(data.get("response") or "").strip()


def generate_stateless_reply(question: str) -> str:
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    return _call_chad(history, question)


def generate_document_reply(document_text: str, filename: str) -> str:
    snippet = document_text.strip()
    if len(snippet) > MAX_DOCUMENT_CHARS:
        snippet = snippet[:MAX_DOCUMENT_CHARS] + "\n\n[…текст обрезан…]"

    history = [
        {"role": "system", "content": DOCUMENT_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Имя файла: {filename}\n\nТекст документа:\n{snippet}",
        },
    ]
    return _call_chad(history, "Кратко опиши документ и перечисли ключевые факты.")
