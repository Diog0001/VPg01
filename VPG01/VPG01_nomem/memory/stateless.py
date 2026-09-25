from pathlib import Path

from documents.loaders import extract_text
from llm import generate_document_reply, generate_stateless_reply


class StatelessBrain:
    """Ответы без истории диалога и без векторной базы."""

    def answer(self, user_id: int, question: str) -> str:
        _ = user_id
        return generate_stateless_reply(question)

    def summarize_document(self, path: Path, filename: str) -> str:
        text = extract_text(path)
        if not text.strip():
            raise ValueError("В файле не нашлось текста, который можно разобрать.")
        return generate_document_reply(text, filename)
