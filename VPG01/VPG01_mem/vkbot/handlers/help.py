"""Справка и меню."""

from vkbottle.bot import Message

from vkbot.config import labeler
from vkbot.keyboards import BTN_HELP, BTN_MENU, HELP_TEXT, WELCOME_TEXT
from vkbot.service import reset_state, send_text


@labeler.message(text=["/start", "Начать", "начать", "Start"])
async def start_handler(message: Message) -> None:
    await reset_state(message)
    await send_text(message, WELCOME_TEXT)


@labeler.message(text=["/help", BTN_HELP, "помощь", "Help", BTN_MENU, "меню"])
async def help_handler(message: Message) -> None:
    await reset_state(message)
    await send_text(message, HELP_TEXT)
