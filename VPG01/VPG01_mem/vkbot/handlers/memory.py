"""Кнопки памяти: сохранить, статус, очистить, забыть."""

import asyncio

from vkbottle.bot import Message

from vkbot.config import labeler
from vkbot.keyboards import BTN_CLEAR, BTN_FORGET, BTN_MEMORY, BTN_SAVE, YES_NO_KEYBOARD
from vkbot.service import get_brain, reset_state, send_text, user_id
from vkbot.states import BotStates


@labeler.message(text=["/save", BTN_SAVE, "сохранить диалог"])
async def save_handler(message: Message) -> None:
    await reset_state(message)
    brain = get_brain()
    saved, indexed = await asyncio.to_thread(brain.save_dialog, user_id(message))
    if saved == 0:
        await send_text(message, "Пока нечего сохранять: напишите хотя бы одно сообщение.")
        return
    await send_text(
        message,
        "Диалог сохранён.\n"
        f"Реплик из SQLite: {saved}.\n"
        f"Фрагментов в долгой памяти: {indexed}.\n"
        "Диалог уже в SQLite; в Chroma добавлено для семантического поиска.",
    )


@labeler.message(text=["/memory", BTN_MEMORY, "память"])
async def memory_handler(message: Message) -> None:
    await reset_state(message)
    status = await asyncio.to_thread(get_brain().status, user_id(message))
    await send_text(message, status)


@labeler.message(text=["/clear", BTN_CLEAR, "очистить чат"])
async def ask_clear(message: Message) -> None:
    await message.state_dispenser.set(message.peer_id, BotStates.CONFIRM_CLEAR)
    await send_text(
        message,
        "Очистить контекст диалога в SQLite? Документы в Chroma останутся.",
        keyboard=YES_NO_KEYBOARD,
    )


@labeler.message(text=["/forget", BTN_FORGET, "забыть документы"])
async def ask_forget(message: Message) -> None:
    await message.state_dispenser.set(message.peer_id, BotStates.CONFIRM_FORGET)
    await send_text(
        message,
        "Удалить все документы из долгой памяти, включая сохранённый диалог?",
        keyboard=YES_NO_KEYBOARD,
    )
