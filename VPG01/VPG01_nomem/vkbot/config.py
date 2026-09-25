"""Labeler и состояния Long Poll. Токен берётся из корневого config."""

from vkbottle import BuiltinStateDispenser
from vkbottle.bot import BotLabeler

labeler = BotLabeler()
state_dispenser = BuiltinStateDispenser()
