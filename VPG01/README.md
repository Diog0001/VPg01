# VPG01 — две версии бота

Один репозиторий, два проекта на базе VPf09 (эталон лежит рядом в `VPf09/`, в git не входит).

| Каталог | Описание |
|---------|----------|
| [VPG01_nomem](VPG01_nomem/) | Бот **без памяти** между сообщениями |
| [VPG01_mem](VPG01_mem/) | Бот с **SQLite** (вся история) + **ChromaDB** (документы) |

Сравнение версий и сценарии проверки: [COMPARISON.md](COMPARISON.md).

## Быстрый старт

```powershell
cd VPG01_nomem
pip install -r requirements.txt
copy .env.example .env
python bot.py

cd ..\VPG01_mem
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

Для одновременного запуска в Telegram задайте **разные** `TELEGRAM_BOT_TOKEN` в `.env` каждой версии.
