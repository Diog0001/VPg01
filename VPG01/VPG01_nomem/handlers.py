from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from config import TELEGRAM_MAX_MESSAGE, UPLOADS_DIR
from documents.loaders import SUPPORTED_SUFFIXES
from keyboard import BTN_HELP, BUTTON_LABELS, document_save_keyboard, main_keyboard
from memory.stateless import StatelessBrain

START_TEXT = """Привет! Я бот без памяти между сообщениями.

Каждый ваш текст обрабатывается отдельно — я не помню, что вы писали раньше.
PDF, DOCX и TXT можно разобрать один раз: после ответа по файлу нужно прислать его снова, чтобы спросить ещё раз.
"""

HELP_TEXT = """Как это работает

1. Пишите обычные сообщения — каждый ответ только по текущему тексту.
2. Отправьте PDF / DOCX / TXT и нажмите «Разобрать файл» — один ответ по содержимому.
3. Память, сохранение диалога и база документов в этой версии отключены.

Команда: /help
"""


def _brain(context: ContextTypes.DEFAULT_TYPE) -> StatelessBrain:
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


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()
    if not question:
        return

    if question in BUTTON_LABELS:
        if question == BTN_HELP:
            await help_command(update, context)
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
        f"Файл «{filename}» скачан. Разобрать один раз без сохранения в память?",
        reply_markup=document_save_keyboard(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    await query.answer()
    user_id = _user_id(update)
    brain = _brain(context)

    if not query.data.startswith("doc:"):
        return

    _, _, choice = query.data.partition(":")
    pending = context.user_data.pop("pending_document", None)
    if choice != "save":
        await query.edit_message_text("Файл не разобран.")
        return
    if not pending:
        await query.edit_message_text("Нет файла, ожидающего разбора. Пришлите документ ещё раз.")
        return
    try:
        reply = brain.summarize_document(Path(pending["path"]), pending["filename"])
    except Exception as error:
        await query.edit_message_text(f"Не удалось разобрать документ: {error}")
        return
    suffix = (
        "\n\nПовторные вопросы по этому файлу без новой загрузки не поддерживаются."
    )
    await query.edit_message_text(f"{reply}{suffix}")


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        "Пришли текст или файл PDF / DOCX / TXT. Картинки и голосовые пока не разбираю.",
    )
