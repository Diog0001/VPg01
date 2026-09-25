from pathlib import Path
import os
import urllib.request

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY", "").strip()
VK_TOKEN = os.getenv("VK_TOKEN", "").strip()

# Ключ из https://ask.chadgpt.ru/profile/public-api
CHAD_API_KEY = os.getenv("CHAD_API_KEY", "").strip()
CHAD_API_BASE = os.getenv("CHAD_API_BASE", "https://ask.chadgpt.ru/api/public").strip()
CHAD_MODEL = os.getenv("CHAD_MODEL", "gpt-5-mini").strip()

DATA_DIR = ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
CONTEXT_DB = DATA_DIR / "context.db"
SHORT_DIR = DATA_DIR / "short"

# Память VK отдельно от Telegram: одинаковые числовые id не делят диалог
VK_DATA_DIR = DATA_DIR / "vk"
VK_UPLOADS_DIR = VK_DATA_DIR / "uploads"
VK_CHROMA_DIR = VK_DATA_DIR / "chroma"
VK_CONTEXT_DB = VK_DATA_DIR / "context.db"
VK_SHORT_DIR = VK_DATA_DIR / "short"

# Максимум символов истории в system prompt (в БД хранятся все реплики)
CONTEXT_PROMPT_MAX_CHARS = int(os.getenv("CONTEXT_PROMPT_MAX_CHARS", "80000"))

# Долгая память: сколько фрагментов документа подмешивать в промпт
RAG_TOP_K = 4
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

TELEGRAM_MAX_MESSAGE = 4000
VK_MAX_MESSAGE = 3500


def resolve_telegram_proxy() -> str | None:
    """Явный TELEGRAM_PROXY или системный прокси Windows (Clash/V2Ray).

    Значения none/off/direct отключают прокси.
    """
    if TELEGRAM_PROXY:
        if TELEGRAM_PROXY.lower() in {"none", "off", "direct"}:
            return None
        return TELEGRAM_PROXY

    proxies = urllib.request.getproxies()
    proxy = (proxies.get("https") or proxies.get("http") or "").strip()
    return proxy or None


def ensure_data_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    CONTEXT_DB.parent.mkdir(parents=True, exist_ok=True)


def ensure_vk_dirs() -> None:
    VK_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    VK_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    VK_CONTEXT_DB.parent.mkdir(parents=True, exist_ok=True)


def validate_config() -> None:
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not CHAD_API_KEY:
        missing.append("CHAD_API_KEY")
    if missing:
        raise SystemExit(
            "Не заданы переменные окружения: "
            + ", ".join(missing)
            + "\nСкопируйте .env.example в .env и заполните значения."
        )


def validate_vk_config() -> None:
    missing = []
    if not VK_TOKEN:
        missing.append("VK_TOKEN")
    if not CHAD_API_KEY:
        missing.append("CHAD_API_KEY")
    if missing:
        raise SystemExit(
            "Не заданы переменные окружения: "
            + ", ".join(missing)
            + "\nСкопируйте .env.example в .env и заполните значения."
        )
