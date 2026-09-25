"""Разбор ответов «да/нет» и нарезка длинных сообщений VK."""

YES_WORDS = {"да", "yes", "y", "д", "сохранить"}
NO_WORDS = {"нет", "no", "n", "н", "отмена"}


def choice(text: str) -> str | None:
    word = text.strip().lower()
    if word in YES_WORDS:
        return "yes"
    if word in NO_WORDS:
        return "no"
    return None


def split_text(text: str, limit: int) -> list[str]:
    body = (text or "").strip() or "Пустой ответ."
    return [body[start : start + limit] for start in range(0, len(body), limit)]


def safe_filename(title: str, ext: str = "") -> str:
    name = (title or "document").replace("\\", "/").split("/")[-1].strip() or "document"
    suffix = f".{ext.lstrip('.').lower()}" if ext else ""
    if suffix and not name.lower().endswith(suffix):
        name = f"{name}{suffix}"
    return name
