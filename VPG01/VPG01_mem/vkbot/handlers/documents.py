"""Подтверждения и загрузка документов."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from vkbottle.bot import Message
from vkbottle.dispatch.rules.abc import ABCRule

from documents.loaders import SUPPORTED_SUFFIXES
from vkbot.config import labeler
from vkbot.keyboards import DOC_KEYBOARD
from vkbot.service import answer_question, download_doc, get_brain, reset_state, send_text, user_id
from vkbot.states import BotStates
from vkbot.textutil import choice, safe_filename

logger = logging.getLogger(__name__)


class HasDocRule(ABCRule[Message]):
    async def check(self, event: Message) -> bool:
        return any(getattr(item, "doc", None) for item in (event.attachments or []))


@labeler.message(HasDocRule())
async def document_handler(message: Message) -> None:
    doc = next(item.doc for item in message.attachments or [] if getattr(item, "doc", None))
    filename = safe_filename(getattr(doc, "title", "") or "document", getattr(doc, "ext", "") or "")
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        await send_text(message, "Поддерживаются только PDF, DOCX и TXT.")
        return
    url = getattr(doc, "url", "") or ""
    if not url:
        await send_text(message, "У файла нет ссылки на скачивание. Пришлите его ещё раз.")
        return
    try:
        path = await download_doc(url, user_id(message), filename)
    except Exception as error:
        logger.exception("Не удалось скачать документ VK")
        await send_text(message, f"Не удалось скачать файл: {error}")
        return
    await message.state_dispenser.set(
        message.peer_id,
        BotStates.CONFIRM_DOC,
        path=str(path),
        filename=filename,
    )
    await send_text(
        message,
        f"Файл «{filename}» скачан. Сохранить в долгую память?",
        keyboard=DOC_KEYBOARD,
    )


@labeler.message(state=BotStates.CONFIRM_CLEAR)
async def confirm_clear(message: Message) -> None:
    picked = choice(message.text or "")
    await reset_state(message)
    if picked == "yes":
        await asyncio.to_thread(get_brain().clear_dialog, user_id(message))
        await send_text(message, "Контекст диалога в SQLite очищен. Документы в Chroma на месте.")
        return
    if picked == "no":
        await send_text(message, "Очистка отменена.")
        return
    await send_text(message, "Очистка отменена. Отвечаю на сообщение.")
    await answer_question(message, (message.text or "").strip())


@labeler.message(state=BotStates.CONFIRM_FORGET)
async def confirm_forget(message: Message) -> None:
    picked = choice(message.text or "")
    await reset_state(message)
    if picked == "yes":
        await asyncio.to_thread(get_brain().long.clear, user_id(message))
        await send_text(message, "Долгая память очищена. Документы удалены из векторной базы.")
        return
    if picked == "no":
        await send_text(message, "Удаление документов отменено.")
        return
    await send_text(message, "Удаление отменено. Отвечаю на сообщение.")
    await answer_question(message, (message.text or "").strip())


@labeler.message(state=BotStates.CONFIRM_DOC)
async def confirm_doc(message: Message) -> None:
    state = await message.state_dispenser.get(message.peer_id)
    payload = dict(state.payload) if state and state.payload else {}
    picked = choice(message.text or "")
    await reset_state(message)
    if picked != "yes":
        if picked == "no":
            await send_text(message, "Файл не сохранён в долгую память.")
        else:
            await send_text(message, "Сохранение файла отменено. Отвечаю на сообщение.")
            text = (message.text or "").strip()
            if text:
                await answer_question(message, text)
        return
    path = payload.get("path")
    filename = str(payload.get("filename") or "document")
    if not path:
        await send_text(message, "Нет файла, ожидающего сохранения. Пришлите документ ещё раз.")
        return
    try:
        chunks = await asyncio.to_thread(
            get_brain().remember_file, user_id(message), Path(path), filename
        )
    except Exception as error:
        await send_text(message, f"Не удалось сохранить документ: {error}")
        return
    await send_text(
        message,
        f"Документ «{filename}» сохранён в долгую память.\n"
        f"Фрагментов: {chunks}.\n"
        "Можно спрашивать по содержимому.",
    )
