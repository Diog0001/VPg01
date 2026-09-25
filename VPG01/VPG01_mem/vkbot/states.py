"""Состояния подтверждения в VK-боте."""

from vkbottle import BaseStateGroup


class BotStates(BaseStateGroup):
    CONFIRM_CLEAR = "confirm_clear"
    CONFIRM_FORGET = "confirm_forget"
    CONFIRM_DOC = "confirm_doc"
