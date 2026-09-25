"""Точка входа VK-бота с памятью. Long Poll через vkbottle."""

from __future__ import annotations

import logging
import signal
import sys

from vkbottle.bot import Bot

from config import VK_TOKEN, ensure_vk_dirs, validate_vk_config
from vkbot.config import labeler, state_dispenser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    validate_vk_config()
    ensure_vk_dirs()
    import vkbot.handlers  # noqa: F401 — регистрация хендлеров

    return Bot(token=VK_TOKEN, labeler=labeler, state_dispenser=state_dispenser)


def main() -> int:
    try:
        bot = create_bot()
    except SystemExit as exc:
        logger.error("%s", exc)
        return 1

    def shutdown_handler(signum: int, _frame: object) -> None:
        logger.info("Получен сигнал %s, завершение работы...", signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown_handler)

    logger.info("VK-бот запущен (Long Poll). Нажмите Ctrl+C для остановки.")
    bot.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
