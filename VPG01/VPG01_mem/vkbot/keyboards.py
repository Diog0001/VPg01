"""Клавиатура VK: те же действия, что у Telegram-бота."""

from vkbottle import Keyboard, KeyboardButtonColor, Text

BTN_SAVE = "Сохранить диалог"
BTN_MEMORY = "Память"
BTN_CLEAR = "Очистить чат"
BTN_FORGET = "Забыть документы"
BTN_HELP = "Помощь"
BTN_MENU = "Меню"

HELP_TEXT = """Как пользоваться

Пишите обычный текст — все реплики сохраняются в SQLite и попадают в системный промпт.

Кнопки
• Сохранить диалог — проиндексировать чат в ChromaDB
• Память — статус SQLite и документов
• Очистить чат — сбросить контекст в SQLite
• Забыть документы — удалить файлы из ChromaDB

Команды: /help, /save, /memory, /clear, /forget.
Файл PDF, DOCX или TXT — бот спросит, сохранять ли его.
"""

WELCOME_TEXT = (
    "Привет! Я бот с долговременной памятью.\n\n"
    "Вся история диалога хранится в SQLite и переживает перезапуск. "
    "PDF, DOCX и TXT можно положить в векторную базу ChromaDB.\n\n"
    + HELP_TEXT
)

MAIN_KEYBOARD = (
    Keyboard(one_time=False, inline=False)
    .add(Text(BTN_SAVE), color=KeyboardButtonColor.PRIMARY)
    .add(Text(BTN_MEMORY))
    .row()
    .add(Text(BTN_CLEAR), color=KeyboardButtonColor.NEGATIVE)
    .add(Text(BTN_FORGET), color=KeyboardButtonColor.SECONDARY)
    .row()
    .add(Text(BTN_HELP), color=KeyboardButtonColor.SECONDARY)
    .get_json()
)

YES_NO_KEYBOARD = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Да"), color=KeyboardButtonColor.POSITIVE)
    .add(Text("Нет"), color=KeyboardButtonColor.NEGATIVE)
    .get_json()
)

DOC_KEYBOARD = (
    Keyboard(one_time=True, inline=False)
    .add(Text("Сохранить"), color=KeyboardButtonColor.POSITIVE)
    .add(Text("Отмена"), color=KeyboardButtonColor.NEGATIVE)
    .get_json()
)
