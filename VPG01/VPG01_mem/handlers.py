from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from config import TELEGRAM_MAX_MESSAGE, UPLOADS_DIR
from documents.loaders import SUPPORTED_SUFFIXES
from keyboard import (
    BTN_CLEAR,
    BTN_FORGET,
    BTN_MEMORY,
    BTN_SAVE,
    BUTTON_LABELS,
    confirm_keyboard,
    document_save_keyboard,
    main_keyboard,
)
from memory.brain import MemoryBrain

START_TEXT = """Привет! Я бот с долговременной памятью.

Контекст диалога
Все реплики автоматически сохраняются в SQLite и подмешиваются в системный промпт — после перезапуска бота диалог продолжается.

Долгая память
Пришли PDF, DOCX или TXT — предложу сохранить файл в векторную базу ChromaDB. Кнопка «Сохранить диалог» дублирует чат в векторную базу для поиска.

Кнопки: сохранить диалог, память, очистить чат, забыть документы.
"""

HELP_TEXT = """Как это работает

1. Пиши обычные сообщения — каждая реплика пишется в SQLite и попадает в системный промпт.
2. Перезапусти бота — сохранённые реплики подгрузятся из базы.
3. «Сохранить диалог» — дополнительно индексирует чат в ChromaDB.
4. Отправь PDF / DOCX / TXT и подтверди сохранение в векторную базу.

Команды: /memory, /clear, /forget, /save.
"""


def _brain(context: ContextTypes.DEFAULT_TYPE) -> MemoryBrain:
    return context.application.bot_data["brain"]


def _user_id(update: Update) -> int:
    if update.effective_user is None:
        raise RuntimeError("Не удалось определить пользователя.")
    return update.effective_user.id


async def _reply(update: Update, text: str) -> None:
    if not update.message:
        return
    if not text:
        text = "Пустой ответ модели."
    markup = main_keyboard()
    chunks = [
        text[start : start + TELEGRAM_MAX_MESSAGE]
        for start in range(0, len(text), TELEGRAM_MAX_MESSAGE)
    ]
    for index, chunk in enumerate(chunks):
        await update.message.reply_text(
            chunk,
            reply_markup=markup if index == len(chunks) - 1 else None,
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, START_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, HELP_TEXT)


async def memory_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await _reply(update, _brain(context).status(_user_id(update)))


async def save_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    saved, indexed = _brain(context).save_dialog(_user_id(update))
    if saved == 0:
        await _reply(update, "Пока нечего сохранять: напишите хотя бы одно сообщение.")
        return
    await _reply(
        update,
        "Диалог проиндексирован в Chroma.\n"
        f"Реплик из SQLite: {saved}.\n"
        f"Фрагментов в долгой памяти: {indexed}.\n"
        "Диалог уже в SQLite; в Chroma добавлено для семантического поиска.",
    )


async def ask_clear_short(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Очистить контекст диалога в SQLite? Документы в Chroma останутся.",
        reply_markup=confirm_keyboard("clear"),
    )


async def ask_forget_docs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Удалить все документы из долгой памяти, включая сохранённый диалог?",
        reply_markup=confirm_keyboard("forget"),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()
    if not question:
        return

    if question in BUTTON_LABELS:
        if question == BTN_SAVE:
            await save_dialog(update, context)
        elif question == BTN_MEMORY:
            await memory_status(update, context)
        elif question == BTN_CLEAR:
            await ask_clear_short(update, context)
        elif question == BTN_FORGET:
            await ask_forget_docs(update, context)
        return

    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        reply = _brain(context).answer(_user_id(update), question)
    except Exception as error:
        reply = f"Не получилось ответить: {error}"
    await _reply(update, reply)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.document:
        return

    document = update.message.document
    filename = document.file_name or "document"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        await _reply(update, "Поддерживаются только PDF, DOCX и TXT.")
        return

    user_id = _user_id(update)
    upload_dir = UPLOADS_DIR / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    local_path = upload_dir / filename

    await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    telegram_file = await context.bot.get_file(document.file_id)
    await telegram_file.download_to_drive(custom_path=str(local_path))

    context.user_data["pending_document"] = {
        "path": str(local_path),
        "filename": filename,
    }
    await update.message.reply_text(
        f"Файл «{filename}» скачан. Сохранить в долгую память?",
        reply_markup=document_save_keyboard(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    await query.answer()
    user_id = _user_id(update)
    brain = _brain(context)
    action, _, choice = query.data.partition(":")

    if action == "clear":
        if choice == "yes":
            brain.clear_dialog(user_id)
            text = "Контекст диалога в SQLite очищен. Документы в Chroma на месте."
        else:
            text = "Очистка отменена."
        await query.edit_message_text(text)
        return

    if action == "forget":
        if choice == "yes":
            brain.long.clear(user_id)
            text = "Долгая память очищена. Документы удалены из векторной базы."
        else:
            text = "Удаление документов отменено."
        await query.edit_message_text(text)
        return

    if action == "doc":
        pending = context.user_data.pop("pending_document", None)
        if choice != "save":
            await query.edit_message_text("Файл не сохранён в долгую память.")
            return
        if not pending:
            await query.edit_message_text("Нет файла, ожидающего сохранения. Пришлите документ ещё раз.")
            return
        try:
            chunks = brain.remember_file(user_id, Path(pending["path"]), pending["filename"])
        except Exception as error:
            await query.edit_message_text(f"Не удалось сохранить документ: {error}")
            return
        await query.edit_message_text(
            f"Документ «{pending['filename']}» сохранён в долгую память.\n"
            f"Фрагментов: {chunks}.\n"
            "Можно спрашивать по содержимому."
        )


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        "Пришли текст или файл PDF / DOCX / TXT. Картинки и голосовые пока не разбираю.",
    )
