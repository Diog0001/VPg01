from telegram import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

BTN_HELP = "ℹ️ Помощь"

BUTTON_LABELS = {BTN_HELP}


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_HELP)]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Напиши вопрос",
    )


def document_save_keyboard() -> InlineKeyboardMarkup:
    from telegram import InlineKeyboardButton

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📄 Разобрать файл", callback_data="doc:save"),
                InlineKeyboardButton("Отмена", callback_data="doc:skip"),
            ]
        ]
    )
