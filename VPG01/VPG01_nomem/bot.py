import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

from config import TELEGRAM_BOT_TOKEN, ensure_data_dirs, resolve_telegram_proxy, validate_config
from handlers import (
    handle_callback,
    handle_document,
    handle_text,
    handle_unsupported,
    help_command,
    start,
)
from memory.stateless import StatelessBrain


def _telegram_request() -> HTTPXRequest:
    proxy = resolve_telegram_proxy()
    kwargs = {
        "connect_timeout": 20.0,
        "read_timeout": 30.0,
        "write_timeout": 30.0,
        "pool_timeout": 5.0,
        "http_version": "1.1",
    }
    if proxy:
        kwargs["proxy"] = proxy
        kwargs["httpx_kwargs"] = {"trust_env": False}
    return HTTPXRequest(**kwargs)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    validate_config()
    ensure_data_dirs()

    proxy = resolve_telegram_proxy()
    logging.getLogger(__name__).info(
        "Прокси Telegram: %s", proxy or "не используется"
    )

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(_telegram_request())
        .get_updates_request(_telegram_request())
        .build()
    )
    application.bot_data["brain"] = StatelessBrain()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(~filters.COMMAND, handle_unsupported))

    logging.getLogger(__name__).info("Бот без памяти запущен. Нажмите Ctrl+C для остановки.")
    application.run_polling(drop_pending_updates=True, bootstrap_retries=5)


if __name__ == "__main__":
    main()
