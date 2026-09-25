"""Ответы без памяти и отправка длинных сообщений в VK."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from vkbottle.bot import Message

from config import VK_MAX_MESSAGE, VK_UPLOADS_DIR, ensure_vk_dirs
from memory.stateless import StatelessBrain
from vkbot.keyboards import MAIN_KEYBOARD
from vkbot.textutil import split_text

_brain: StatelessBrain | None = None


def get_brain() -> StatelessBrain:
    global _brain
    if _brain is None:
        ensure_vk_dirs()
        _brain = StatelessBrain()
    return _brain


def user_id(message: Message) -> int:
    return int(message.from_id)


async def reset_state(message: Message) -> None:
    await message.state_dispenser.delete(message.peer_id)


async def send_text(message: Message, text: str, keyboard: str | None = MAIN_KEYBOARD) -> None:
    parts = split_text(text, VK_MAX_MESSAGE)
    for index, part in enumerate(parts):
        await message.answer(part, keyboard=keyboard if index == len(parts) - 1 else None)


async def download_doc(url: str, user: int, filename: str) -> Path:
    folder = VK_UPLOADS_DIR / str(user)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
    path.write_bytes(response.content)
    return path


async def answer_question(message: Message, question: str) -> None:
    brain = get_brain()
    uid = user_id(message)
    try:
        reply = await asyncio.to_thread(brain.answer, uid, question)
    except Exception as error:
        reply = f"Не получилось ответить: {error}"
    await send_text(message, reply)
