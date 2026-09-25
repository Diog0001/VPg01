# VPG01_mem — бот с долговременной памятью

Версия на базе VPf09 для сравнения с `VPG01_nomem`.

## Память

### SQLite (`data/context.db`)

- **Все реплики** диалога пишутся в базу **после каждого ответа** (без обрезки).
- При запуске бот вызывает `warmup()` и логирует, сколько пользователей и реплик уже в базе.
- При каждом запросе вся сохранённая история добавляется в **системный промпт** (если она очень длинная, в промпт попадает хвост — см. `CONTEXT_PROMPT_MAX_CHARS` в `.env`; в БД остаётся полная история).
- `/clear` — принудительный сброс контекста в SQLite (документы в Chroma не трогаются).

### ChromaDB (`data/chroma/`)

- PDF / DOCX / TXT индексируются для RAG (как в VPf09).
- `/save` — дополнительно индексирует текущий диалог из SQLite для семантического поиска.
- `/forget` — удаляет векторную коллекцию пользователя.

## Команды

| Команда | Действие |
|---------|----------|
| `/memory` | Реплики в SQLite + фрагменты и файлы в Chroma |
| `/clear` | Очистить диалог в SQLite |
| `/forget` | Очистить документы в Chroma |
| `/save` | Индексировать диалог в Chroma |

## Проверка после рестарта

1. «Меня зовут Аня, я из Казани.»
2. Остановите бота (Ctrl+C) и снова `python bot.py`.
3. «Как меня зовут?» — ответ должен опираться на SQLite.
4. `/clear` — имя больше не используется.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

VK: `python vk_bot.py`.

## Тесты

```powershell
python -m unittest discover -s tests -v
```

## Структура

```text
memory/sqlite_context.py   SQLite-контекст
memory/long_term.py        ChromaDB
memory/brain.py            склейка SQLite + RAG
llm.py                     системный промпт + контекст из БД
```
