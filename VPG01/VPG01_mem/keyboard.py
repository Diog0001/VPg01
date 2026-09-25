from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

BTN_SAVE = "💾 Сохранить диалог"
BTN_MEMORY = "📊 Память"
BTN_CLEAR = "🧹 Очистить чат"
BTN_FORGET = "🗑 Забыть документы"

BUTTON_LABELS = {BTN_SAVE, BTN_MEMORY, BTN_CLEAR, BTN_FORGET}


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_SAVE), KeyboardButton(BTN_MEMORY)],
            [KeyboardButton(BTN_CLEAR), KeyboardButton(BTN_FORGET)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Напиши вопрос или нажми кнопку",
    )


def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Да", callback_data=f"{action}:yes"),
                InlineKeyboardButton("Отмена", callback_data=f"{action}:no"),
            ]
        ]
    )


def document_save_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💾 Сохранить", callback_data="doc:save"),
                InlineKeyboardButton("Отмена", callback_data="doc:skip"),
            ]
        ]
    )
