"""Регистрация хендлеров. fallback импортируется последним — он ловит весь остальной текст."""

from vkbot.config import labeler
from vkbot.handlers import documents, fallback, help, memory

__all__ = ("labeler",)

_ = (help, memory, documents, fallback)
