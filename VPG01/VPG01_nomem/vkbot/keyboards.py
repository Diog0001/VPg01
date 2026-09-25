"""Клавиатура VK для версии без памяти."""

from vkbottle import Keyboard, KeyboardButtonColor, Text

BTN_HELP = "Помощь"
BTN_MENU = "Меню"

HELP_TEXT = """Как пользоваться

Пишите обычный текст — каждое сообщение обрабатывается отдельно, без истории.

Файл PDF, DOCX или TXT можно разобрать один раз: после ответа пришлите файл снова, если нужны ещё вопросы.

Команды: /help, /start.
"""

WELCOME_TEXT = (
    "Привет! Я бот без памяти между сообщениями.\n\n"
    "Я не помню прошлые реплики. Документы не сохраняю в базу — только одноразовый разбор.\n\n"
    + HELP_TEXT
)

MAIN_KEYBOARD = (
    Keyboard(one_time=False, inline=False)
    .add(Text(BTN_HELP), color=KeyboardButtonColor.SECONDARY)
    .get_json()
)

DOC_KEYBOARD = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Разобрать"), color=KeyboardButtonColor.POSITIVE)
    .add(Text("Отмена"), color=KeyboardButtonColor.NEGATIVE)
    .get_json()
)
