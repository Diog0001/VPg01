"""Обычный текст уходит в комбинированную память."""

from vkbottle.bot import Message

from vkbot.config import labeler
from vkbot.service import answer_question


@labeler.message()
async def chat_handler(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Пришлите текст или файл PDF / DOCX / TXT.")
        return
    await answer_question(message, text)
