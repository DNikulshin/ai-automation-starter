# AI Automation Starter 🤖

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)

> Готовый шаблон для автоматизации бизнес-процессов с использованием LLM (OpenRouter/Claude).  
> Забирает сырые данные → структурирует через AI → сохраняет в Obsidian/Markdown → уведомляет в Telegram.

🔗 **Для нетехнических пользователей**: [📖 Инструкция в USER_GUIDE.md](./docs/USER_GUIDE.md)

---

## ✨ Возможности

| Функция | Описание | Бизнес-ценность |
|---------|----------|-----------------|
| 📥 Умный импорт | Чтение `.txt` из папки, поддержка email/Plaud API (расширяемо) | Не нужно копировать вручную — просто положите файл |
| 🧠 AI-структурирование | LLM выделяет дату, резюме, задачи, теги в валидный JSON | Сырой текст превращается в структурированные данные |
| 📁 Obsidian-ready экспорт | Генерация `.md` с YAML frontmatter, чек-листами, тегами | Результат сразу готов к импорту в Obsidian/Notion |
| 🔔 Telegram-уведомления | Уведомления об успехе/ошибке/старте пайплайна | Заказчик видит, что система работает, без захода в логи |
| 🐳 Docker-упаковка | Запуск в 1 команду, изоляция зависимостей | Развёртывание на любом VPS за 5 минут |
| 🧪 Покрыто тестами | 8 юнит- и интеграционных тестов (pytest) | Уверенность в стабильности при кастомизации |

---

## 🏗 Архитектура

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   data/input/   │     │   src/          │     │  data/output/   │
│  • dental.txt   │────▶│  • ingestion.py │────▶│  • dental.md    │
│  • memo.txt     │     │  • processor.py │     │  • memo.md      │
└─────────────────┘     │  • exporter.py  │     └─────────────────┘
                        │  • pipeline.py  │              │
                        │  • notifier.py  │              ▼
                        └────────┬────────┘     ┌─────────────────┐
                                 │              │   Obsidian /    │
                                 ▼              │   Notion /      │
                        ┌─────────────────┐     │   Confluence    │
                        │  LLM (OpenRouter│     └─────────────────┘
                        │   / Claude API) │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Telegram Bot   │
                        │  (уведомления)  │
                        └─────────────────┘
```

---

## 🚀 Быстрый старт

### ▶️ Локально (без Docker)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/DNikulshin/ai-automation-starter.git
cd ai-automation-starter

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Отредактируйте .env: добавьте OPENROUTER_API_KEY и опционально Telegram-токены

# 5. Запустить пайплайн
python -m src
```

### 🐳 Через Docker (рекомендуется для продакшена)

```bash
# 1. Настроить .env (как выше)
cp .env.example .env

# 2. Запустить сборку и контейнер
docker-compose up -d --build

# 3. Посмотреть логи в реальном времени
docker-compose logs -f ai-automation

# 4. Остановить
docker-compose down
```

> 💡 **Совет**: Для периодического запуска (cron) раскомментируйте строку `command` в `docker-compose.yml`.

---

## ⚙️ Конфигурация (.env)

| Переменная | Обязательна | Описание | Пример |
|------------|-------------|----------|--------|
| `OPENROUTER_API_KEY` | ✅ | Ключ API OpenRouter для доступа к LLM | `sk-or-v1-abc123...` |
| `LLM_MODEL` | ❌ | Модель для обработки (по умолчанию — бесплатная) | `mistralai/mistral-7b-instruct:free` |
| `MAX_RETRIES` | ❌ | Количество повторных попыток при ошибке API | `3` |
| `REQUEST_TIMEOUT` | ❌ | Таймаут запроса к LLM в секундах | `30` |
| `TELEGRAM_BOT_TOKEN` | ❌ | Токен бота для уведомлений (получить у @BotFather) | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | ❌ | ID чата/пользователя для отправки уведомлений | `-1001234567890` |

🔧 **Как получить Telegram Chat ID**: отправьте сообщение боту @userinfobot или добавьте бота в чат и используйте ID чата.

---

## 📁 Структура проекта

```
ai-automation-starter/
├── src/
│   ├── __init__.py          # Пакетная маркировка
│   ├── __main__.py          # Точка входа: python -m src
│   ├── cli.py               # Основная логика запуска
│   ├── config.py            # Валидация настроек (Pydantic)
│   ├── ingestion.py         # Забор данных из input/
│   ├── processor.py         # LLM-обработка + retry + JSON-парсинг
│   ├── exporter.py          # Экспорт в Obsidian-ready Markdown
│   ├── pipeline.py          # Оркестрация: ingestion → process → export
│   └── notifier.py          # Telegram-уведомления
├── prompts/
│   └── default.yaml         # Шаблон системного промпта для LLM
├── tests/
│   ├── test_processor.py    # Юнит-тесты LLM-процессора
│   ├── test_pipeline.py     # E2E-тест всего пайплайна
│   ├── test_notifier.py     # Тесты Telegram-уведомлений
│   └── test_main.py         # Тест точки входа
├── data/                    # Рабочие директории (создаются автоматически)
│   ├── input/               # Сюда кладёте файлы для обработки
│   ├── processed/           # Обработанные исходники (идемпотентность)
│   └── output/              # Готовые .md-файлы
├── logs/
│   └── automation.log       # Логи выполнения
├── .env.example             # Шаблон переменных окружения
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md                # Этот файл
└── docs/
    └── USER_GUIDE.md        # 📖 Инструкция для нетехнического пользователя
```

---

## 🧪 Тестирование

```bash
# Запустить все тесты
pytest tests/ -v

# Запустить с отображением покрытия (требуется pytest-cov)
pytest tests/ -v --cov=src --cov-report=term-missing

# Запустить конкретный тест
pytest tests/test_processor.py::test_process_valid_json -v
```

✅ **Ожидаемый результат**: `8 passed`

---

## 🔧 Кастомизация под заказчика

Проект спроектирован как конвейер: меняйте один модуль — остальное работает.

### 🔄 Заменить источник данных
Отредактируйте `src/ingestion.py`:
```python
# Пример: чтение из email через IMAP
# Добавьте в класс FileIngestion метод:
def fetch_from_email(self, imap_server: str, login: str, password: str):
    # ... логика подключения и скачивания вложений ...
```

### 🎯 Адаптировать промпт под домен
Откройте `prompts/default.yaml` и измените инструкцию:
```yaml
# Для юридической фирмы:
system: "Ты помощник юриста. Отвечай ТОЛЬКО валидным JSON."
template: |
  Извлеки:
  - client_name (ФИО)
  - case_type (гражданское/уголовное/арбитраж)
  - deadline (дата, если есть)
  - next_steps (список действий)
  - tags (3-5 ключевых слов)
  Текст: {text}
```

### 📤 Изменить формат вывода
Правьте `src/exporter.py`:
```python
# Для Notion: замените Markdown-разметку на Notion API calls
# Для Google Docs: добавьте экспорт через google-api-python-client
```

### ⏰ Запуск по расписанию
В `docker-compose.yml` замените `CMD` на:
```yaml
command: ["sh", "-c", "while true; do python -m src; sleep 300; done"]  # каждые 5 минут
```

---

## 🛠 Устранение неполадок

| Проблема | Возможная причина | Решение |
|----------|-------------------|---------|
| `Config validation failed` | Не задан `OPENROUTER_API_KEY` в `.env` | Скопируйте `.env.example` → `.env` и заполните ключ |
| `LLM processing failed after 3 attempts` | Закончились токены / неверный ключ | Проверьте баланс на [openrouter.ai/keys](https://openrouter.ai/keys) |
| Файлы не обрабатываются | Папка `input/` пуста или файлы не `.txt` | Положите `.txt`-файл в `data/input/` |
| Нет уведомлений в Telegram | Неверный токен или бот не добавлен в чат | Проверьте токен у @BotFather, добавьте бота в чат |
| `FileNotFoundError: logs/automation.log` | Папка `logs/` не создана (старая версия) | Обновите `cli.py` — в актуальной версии папка создаётся автоматически |

📋 **Полные логи**: `docker-compose logs ai-automation` или файл `logs/automation.log`

---

## 🤝 Лицензия и использование

Проект распространяется под лицензией **MIT** — используйте в коммерческих проектах, модифицируйте, форкайте.

> 💡 **Для заказчиков**: Этот шаблон — основа. Мы адаптируем его под ваши процессы за 1-3 дня: подключим ваш источник данных, настроим промпт под вашу предметную область, интегрируем с вашей CRM.

---

## 📬 Контакты и поддержка

- 👨‍💻 **Разработчик**: Дмитрий Никульшин
- 🌐 **Портфолио**: [nikulshin-dev.ru](https://dnikulshin.ru)
- 💬 **Telegram**: [@nikulshin_dev](https://t.me/nikulshin_dev)
- 🐙 **GitHub**: [DNikulshin](https://github.com/DNikulshin)
- 📧 **Email**: d.nikulshin.dev@gmail.com

---

> 📖 **Для нетехнических пользователей**: подробная пошаговая инструкция по использованию — в файле [docs/USER_GUIDE.md](./docs/USER_GUIDE.md)

---

*Сделано с ❤️ для автоматизации рутины. Если проект помог — поставьте ⭐ на GitHub.*
