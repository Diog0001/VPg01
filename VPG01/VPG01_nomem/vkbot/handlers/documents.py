"""Загрузка документов (одноразовый разбор)."""

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
        f"Файл «{filename}» скачан. Разобрать один раз без сохранения в память?",
        keyboard=DOC_KEYBOARD,
    )


@labeler.message(state=BotStates.CONFIRM_DOC)
async def confirm_doc(message: Message) -> None:
    state = await message.state_dispenser.get(message.peer_id)
    payload = dict(state.payload) if state and state.payload else {}
    picked = choice(message.text or "")
    await reset_state(message)
    if picked != "yes":
        if picked == "no":
            await send_text(message, "Файл не разобран.")
        else:
            await send_text(message, "Разбор отменён. Отвечаю на сообщение.")
            text = (message.text or "").strip()
            if text:
                await answer_question(message, text)
        return
    path = payload.get("path")
    filename = str(payload.get("filename") or "document")
    if not path:
        await send_text(message, "Нет файла, ожидающего разбора. Пришлите документ ещё раз.")
        return
    try:
        reply = await asyncio.to_thread(
            get_brain().summarize_document, Path(path), filename
        )
    except Exception as error:
        await send_text(message, f"Не удалось разобрать документ: {error}")
        return
    await send_text(
        message,
        f"{reply}\n\nПовторные вопросы по этому файлу без новой загрузки не поддерживаются.",
    )
