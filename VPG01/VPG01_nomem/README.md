# VPG01_nomem — бот без памяти

Версия на базе VPf09 для сравнения с `VPG01_mem`: каждый запрос к модели идёт **без истории диалога** и **без векторной базы**.

## Поведение

- Текстовые сообщения обрабатываются по одному; прошлые реплики не передаются в модель.
- PDF / DOCX / TXT можно **разобрать один раз** (краткое содержание и факты). Повторные вопросы по тому же файлу без новой загрузки не поддерживаются.
- Команды памяти (`/save`, `/memory`, `/clear`, `/forget`) отсутствуют.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

VK: `python vk_bot.py` (нужен `VK_TOKEN` в `.env`).

## Тесты

```powershell
python -m unittest discover -s tests -v
```

## Структура

```text
memory/stateless.py   логика без памяти
llm.py                вызов ChadGPT без history
handlers.py           Telegram
vkbot/                VK Long Poll
```
