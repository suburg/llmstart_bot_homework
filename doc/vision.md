# Техническое видение проекта: ИИ-ассистент для совместного сочинения детских историй

## 1. Технологии

**Основной стек:**
- **Python 3.11+** - основной язык разработки
- **aiogram** - библиотека для Telegram Bot API (асинхронная, современная)
- **polza.ai + OpenAI client** - доступ к различным LLM через единый интерфейс (совместимость с OpenAI API)
- **SQLite** - локальная база данных для хранения историй и текущего прогресса
- **python-dotenv** - управление переменными окружения

**AI-сервисы:**
- **Speech-to-Text API** - распознавание голосовых сообщений (Whisper API или аналоги)
- **Image Generation API** - создание обложек историй (DALL-E, Stable Diffusion или аналоги)
- **Vision API** - анализ загруженных изображений для определения стиля и темы

**Инструменты разработки:**
- **uv** - управление зависимостями (быстрый, современный)
- **pytest** - фреймворк для тестирования
- **Make** - автоматизация сборки и запуска

**Деплой и контейнеризация:**
- **Docker** - контейнеризация для деплоя на облачный VPS
- **VPS** - облачный сервер для развертывания

**Принципы:**
- Никаких дополнительных фреймворков - простой асинхронный скрипт
- SQLite для хранения историй и текущего прогресса (сохранение состояния при перезапуске)
- Максимальная простота и минимализм

## 2. Принципы разработки

- **KISS (Keep It Simple, Stupid)** - максимальная простота решений
- **MVP подход** - минимально жизнеспособный продукт для проверки гипотезы
- **Итеративная разработка** - быстрые циклы: разработка → тестирование → улучшение
- **Модульность** - разделение функциональности на независимые модули
- **Функциональный подход** - без ООП, используем функции и модули
- **"Работающий код важнее чистого кода"** - сначала делаем работающее решение
- **Функциональное тестирование** - тестируем основные пользовательские сценарии
- **Fail Fast** - быстро выявляем проблемы и исправляем
- **Безопасность контента** - фильтрация сексуального контента для детской аудитории

## 3. Структура проекта

```
llmstart_bot_homework/
├── src/
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── commands.py         # обработчики команд (/start, /help, /new_story, /my_stories)
│   │   │   ├── messages.py         # обработчики текстовых и голосовых сообщений
│   │   │   └── utils.py            # вспомогательные функции для handlers
│   │   └── keyboards.py            # клавиатуры для выбора жанра, длительности и т.д.
│   ├── ai/
│   │   ├── llm.py                  # работа с polza.ai/OpenAI API и локальными LLM
│   │   ├── speech.py               # распознавание голоса (настраиваемый сервис)
│   │   ├── image_gen.py            # генерация обложек (настраиваемый сервис)
│   │   └── vision.py               # анализ загруженных изображений (настраиваемый сервис)
│   ├── storage/
│   │   ├── database.py             # работа с SQLite (CRUD операции)
│   │   ├── models.py               # структуры данных для историй
│   │   └── schema.sql              # DDL-скрипт создания таблиц
│   ├── story/
│   │   ├── manager.py              # управление процессом сочинения
│   │   └── formatter.py            # форматирование и финализация истории
│   ├── prompts/
│   │   ├── system.txt              # системный промпт для основного диалога
│   │   ├── storytelling.txt        # промпт для процесса сочинения
│   │   ├── finalization.txt        # промпт для финализации и создания названия
│   │   ├── praise.txt              # промпт для генерации персональной похвалы
│   │   └── cover_generation.txt   # промпт для генерации обложки
│   ├── config.py                   # конфигурация (включая выбор AI-сервисов)
│   └── main.py                     # точка входа
├── tests/
│   ├── test_handlers.py            # тесты обработчиков
│   ├── test_ai.py                  # тесты AI интеграций
│   ├── test_database.py            # тесты БД
│   └── conftest.py                 # настройки pytest
├── data/
│   ├── stories.db                  # файл SQLite базы данных
│   ├── genres.json                 # справочник жанров с описаниями и референсами
│   └── images/
│       ├── uploads/                # загруженные пользователями изображения
│       └── covers/                 # сгенерированные обложки
├── logs/
│   └── bot.log                     # файл логов
├── .env.example                    # пример переменных окружения
├── Dockerfile
├── Makefile
├── pyproject.toml                  # конфигурация uv
└── README.md
```

## 4. Архитектура проекта

**Компоненты:**
1. **Telegram Bot Handler** - принимает сообщения, отправляет ответы, обрабатывает команды
2. **AI Services** - взаимодействие с различными AI API (LLM, Speech-to-Text, Image Generation, Vision)
3. **Story Manager** - управление процессом сочинения истории (состояние, очередность, завершение)
4. **Database Storage** - хранение историй и текущего прогресса в SQLite
5. **Story Formatter** - финализация, создание названия и компиляция истории

**Поток данных (создание новой истории):**
```
User: /new_story → Bot Handler → Story Manager (создание сессии) →
→ Database (сохранение параметров) → Bot: запрос жанра/героя/кто начинает/уровень креативности →
→ User: выбор параметров (жанр, длительность, герои, кто пишет первым, уровень креативности) →
→ Database (обновление сессии) → Story Manager: начало истории →
→ [если бот начинает: LLM (с выбранной температурой) → Bot: первые предложения]
→ [если пользователь начинает: Bot: просьба начать историю]
```

**Поток данных (процесс сочинения):**
```
User Message/Voice → Bot Handler →
→ [если Voice: Speech-to-Text API] → текст →
→ Story Manager (добавление в историю) → Database (сохранение) →
→ LLM (генерация продолжения с учетом стиля) → 
→ Story Manager (проверка длины) →
→ [если приближается конец: предложение завершить] →
→ Database (сохранение) → Bot Handler → User
```

**Поток данных (завершение истории):**
```
Story Manager (обнаружение приближения конца) →
→ Bot: "История подходит к концу. Завершаем?" →
→ User: подтверждение →
→ LLM (финализация текста с учетом подтверждения) → 
→ LLM (генерация названия) →
→ Image Generation API (создание обложки) →
→ Story Formatter (компиляция) →
→ LLM (генерация похвалы) →
→ Database (сохранение финальной версии) →
→ Bot Handler → User (текст + обложка + похвала)
```

**Принципы архитектуры:**
- Модульная структура с независимыми компонентами
- Story Manager как центральный координатор процесса
- Все состояние персистентно в БД (переживает перезапуски)
- AI-сервисы изолированы и взаимозаменяемы
- Пользователь контролирует ключевые моменты (параметры истории, завершение)
- Прямые вызовы функций без сложных паттернов

## 5. Модель данных

**Структуры данных в БД (SQLite):**

```sql
# Таблица историй
CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- Telegram user ID (chat_id) пользователя
    title TEXT,                                   -- Название истории (генерируется после завершения)
    genre TEXT NOT NULL,                          -- Жанр истории (сказка, приключение, фантастика, детектив)
    duration TEXT NOT NULL                        -- Длительность: 'short', 'medium', 'long'
        CHECK(duration IN ('short', 'medium', 'long')),
    main_hero TEXT NOT NULL,                      -- Имя главного героя
    additional_heroes TEXT,                       -- Дополнительные персонажи (опционально)
    who_starts TEXT NOT NULL                      -- Кто пишет первым: 'bot' или 'user'
        CHECK(who_starts IN ('bot', 'user')),
    creativity_level TEXT NOT NULL                -- Уровень креативности: 'low', 'medium', 'high'
        CHECK(creativity_level IN ('low', 'medium', 'high')),
    status TEXT NOT NULL                          -- Статус: 'in_progress', 'completed', 'abandoned'
        CHECK(status IN ('in_progress', 'completed', 'abandoned')),
    content TEXT,                                 -- JSON массив сообщений процесса сочинения
    final_text TEXT,                              -- Финальная скомпилированная версия истории
    cover_url TEXT,                               -- Относительный путь к сгенерированной обложке
    praise_text TEXT,                             -- Текст похвалы от бота для ребенка
    initial_image_url TEXT,                       -- Относительный путь к загруженному пользователем изображению
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- Дата и время создания истории
    completed_at TIMESTAMP                        -- Дата и время завершения истории
);

# Индексы
CREATE INDEX idx_stories_user_id ON stories(user_id);
CREATE INDEX idx_stories_status ON stories(status);
```

**Структура content (JSON):**
```python
# Массив сообщений в процессе сочинения
[
    {"role": "user", "content": "Жил-был храбрый рыцарь...", "timestamp": "..."},
    {"role": "assistant", "content": "Он отправился в далекое путешествие...", "timestamp": "..."},
    ...
]
```

**Хранение изображений (файловая система):**
```
data/
├── stories.db
└── images/
    ├── uploads/          # загруженные пользователями изображения
    │   └── {user_id}_{story_id}_{timestamp}.jpg
    └── covers/           # сгенерированные обложки
        └── {story_id}.png
```

**Конфигурация (из переменных окружения):**
```python
config = {
    # Telegram
    "telegram_token": getenv("TELEGRAM_BOT_TOKEN"),
    
    # LLM (polza.ai или другой OpenAI-compatible сервис)
    "llm_api_key": getenv("LLM_API_KEY"),
    "llm_base_url": getenv("LLM_BASE_URL", "https://api.polza.ai/v1"),
    "llm_model": getenv("LLM_MODEL", "openai/gpt-4o-mini"),
    
    # Speech-to-Text (OpenAI-compatible API)
    "speech_api_key": getenv("SPEECH_API_KEY"),
    "speech_base_url": getenv("SPEECH_BASE_URL", "https://api.openai.com/v1"),
    "speech_model": getenv("SPEECH_MODEL", "whisper-1"),
    
    # Image Generation (OpenAI-compatible API)
    "image_gen_api_key": getenv("IMAGE_GEN_API_KEY"),
    "image_gen_base_url": getenv("IMAGE_GEN_BASE_URL", "https://api.openai.com/v1"),
    "image_gen_model": getenv("IMAGE_GEN_MODEL", "dall-e-3"),
    
    # Vision (OpenAI-compatible API)
    "vision_api_key": getenv("VISION_API_KEY"),
    "vision_base_url": getenv("VISION_BASE_URL", "https://api.openai.com/v1"),
    "vision_model": getenv("VISION_MODEL", "gpt-4o-mini"),
    
    # Database
    "db_path": getenv("DB_PATH", "data/stories.db"),
    
    # Хранение файлов
    "images_base_path": getenv("IMAGES_BASE_PATH", "data/images"),
    "max_image_size_mb": int(getenv("MAX_IMAGE_SIZE_MB", "5")),
    
    # Настройки историй (количество ПАР: user + assistant = 1 пара)
    # После достижения лимита бот предлагает завершить, но пользователь может продолжить
    "max_pairs_short": int(getenv("MAX_PAIRS_SHORT", "5")),    # ~5 пар (примерно)
    "max_pairs_medium": int(getenv("MAX_PAIRS_MEDIUM", "10")), # ~10 пар (примерно)
    "max_pairs_long": int(getenv("MAX_PAIRS_LONG", "20")),     # ~20 пар (примерно)
    
    # Настройки креативности (температура LLM для разных уровней)
    "creativity_low": float(getenv("CREATIVITY_LOW", "0.5")),      # Более предсказуемо
    "creativity_medium": float(getenv("CREATIVITY_MEDIUM", "0.7")), # Сбалансировано
    "creativity_high": float(getenv("CREATIVITY_HIGH", "0.9")),     # Более креативно
    
    # Логирование
    "log_level": getenv("LOG_LEVEL", "INFO"),
}
```

**Принципы:**
- БД для постоянного хранения всех данных
- JSON для гибкого хранения массивов сообщений
- Изображения хранятся в файловой системе, в БД только относительные пути
- История хранится поэтапно: content во время сочинения, final_text после завершения
- Все AI-сервисы используют OpenAI-compatible API для простоты
- Разные API ключи для разных сервисов (гибкость провайдеров)
- status = 'abandoned' при старте новой истории или после 7 дней неактивности

## 6. Работа с LLM

**Интеграция с LLM:**
- **polza.ai** как основной провайдер (совместимость с OpenAI API)
- **OpenAI Client** для унифицированного API
- **Локальные LLM** как альтернатива (опционально, через OpenAI-compatible интерфейс)
- **Модель**: настраивается в конфигурации (по умолчанию `openai/gpt-4o-mini`)

**Функционал `ai/llm.py`:**
```python
async def generate_text(messages: list, model: str = None, temperature: float = 0.7) -> str:
    """Асинхронная генерация текста через LLM API"""
    # model берется из конфигурации если не указан
    # Поддержка polza.ai, OpenAI и локальных моделей через OpenAI-compatible API
    
async def generate_story_continuation(
    story_content: list, 
    creativity_level: str,  # 'low', 'medium', 'high'
    is_ending: bool = False
) -> str:
    """Генерация продолжения истории с учетом стиля пользователя"""
    # Загрузка промпта из prompts/storytelling.txt
    # Загрузка temperature из конфигурации на основе creativity_level
    # temperature = config[f"creativity_{creativity_level}"]
    # Адаптация под стиль пользователя
    # Если is_ending=True, подводит к завершению
    
async def finalize_story(story_content: list, creativity_level: str) -> dict:
    """Финализация истории: генерация названия, финального текста и похвалы"""
    # Загрузка промпта из prompts/finalization.txt
    # Использует соответствующую температуру
    # Возвращает: {"title": "...", "final_text": "...", "praise": "..."}
    
async def generate_praise(story_content: list, params: dict) -> str:
    """Генерация персональной похвалы для ребенка"""
    # Загрузка промпта из prompts/praise.txt
    # Анализ вклада пользователя (только сообщения с role="user")
    # Выделение лучших идей и креативных моментов
    # Использует температуру 0.75 для баланса креативности и предсказуемости
```

**Работа с промптами:**
```python
# Промпты загружаются из файлов в prompts/
def load_prompt(filename: str) -> str:
    """Загрузка промпта из файла"""
    path = f"src/prompts/{filename}"
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# Использование:
system_prompt = load_prompt("system.txt")
storytelling_prompt = load_prompt("storytelling.txt")
finalization_prompt = load_prompt("finalization.txt")
praise_prompt = load_prompt("praise.txt")
cover_prompt = load_prompt("cover_generation.txt")
```

**Принципы:**
- Асинхронная работа для неблокирующей обработки
- Все провайдеры через OpenAI-compatible API (упрощение)
- Специализированные функции для разных этапов сочинения
- Промпты в отдельных файлах для удобного редактирования
- Температура (креативность) задается пользователем при создании истории
- Три уровня креативности: low (0.5), medium (0.7), high (0.9)
- Единая обработка ошибок и логирование запросов

## 7. Мониторинг и логирование AI-сервисов

**Простое логирование:**
- Все запросы и ответы AI-сервисов записываются в файл
- Логирование ошибок при работе с API
- Отслеживание использования токенов (для оптимизации расходов)

**Реализация:**
```python
# В ai/llm.py логировать запросы
async def generate_text(...):
    logger.info(f"LLM Request: {len(messages)} messages, temp={temperature}, model={model}")
    # ... запрос к LLM
    logger.info(f"LLM Response: {len(response)} chars, tokens={usage}")
    logger.error(f"LLM Error: {error}") # при ошибках

# В ai/speech.py
async def transcribe_voice(...):
    logger.info(f"Speech-to-Text Request: file_size={size}kb")
    logger.info(f"Speech-to-Text Response: {len(text)} chars")
    
# В ai/image_gen.py
async def generate_cover(...):
    logger.info(f"Image Generation Request: prompt_length={len(prompt)}")
    logger.info(f"Image Generation Response: url={url}")
```

**Принципы:**
- Никаких внешних систем мониторинга
- Простое логирование в файл
- Отслеживание использования ресурсов
- Минималистичный подход для MVP

## 8. Сценарии работы

**Основные сценарии:**

1. **Первое знакомство**
   - Пользователь отправляет первое сообщение (любое)
   - Бот автоматически отправляет приветствие + краткое описание возможностей
   - Команда `/start` также показывает приветствие
   - Бот предлагает начать новую историю

2. **Создание новой истории**
   - Пользователь: `/new_story`
   - Бот: показывает расширенный справочник жанров с описаниями и референсными произведениями
   - Пользователь выбирает жанр
   - Бот: запрос длительности (короткая ~5 пар, средняя ~10 пар, длинная ~20 пар)
   - Бот: запрос имени главного героя
   - Бот: запрос дополнительных персонажей (опционально)
   - Бот: запрос кто начинает (бот или пользователь)
   - Бот: запрос уровня креативности (спокойная история / обычная / очень креативная)
   - Бот: опция загрузить изображение для вдохновения (опционально)
   - История начинается согласно выбранным параметрам

3. **Процесс сочинения**
   - Пользователь и бот по очереди добавляют по 2-3 предложения
   - Пользователь может писать текстом или голосом
   - Бот адаптируется под стиль пользователя и следует жанру
   - При приближении к заданной длительности бот предупреждает

4. **Завершение истории**
   - Бот: "История подходит к концу. Хочешь завершить или продолжить?"
   - Пользователь выбирает: завершить или написать еще
   - При выборе "завершить": бот создает финальную версию
   - Бот генерирует название и обложку (с учетом жанра и референсов)
   - Бот хвалит ребенка и отмечает лучшие идеи
   - История сохраняется в БД

5. **Просмотр сохраненных историй**
   - Пользователь: `/my_stories`
   - Бот: показывает список историй с названиями, жанрами и датами
   - Пользователь может выбрать историю для просмотра или удаления
   - При просмотре: бот отправляет полный текст и обложку
   - При удалении: бот запрашивает подтверждение, затем удаляет из БД

6. **Удаление истории**
   - Из списка `/my_stories` → выбор истории → кнопка "Удалить"
   - Бот: "Точно удалить историю '[название]'?"
   - Пользователь подтверждает
   - Бот удаляет историю и файлы (обложку, загруженное изображение)

7. **Помощь**
   - Пользователь: `/help`
   - Бот: описание команд, жанров и возможностей

**Поддерживаемые команды:**
- `/start` - приветствие и описание возможностей
- `/new_story` - создание новой истории
- `/my_stories` - просмотр и управление сохраненными историями
- `/help` - помощь и описание возможностей

**Справочник жанров:**
- Хранится в файле `data/genres.json`
- Для каждого жанра: название, описание, референсные произведения
- Примеры жанров: сказка, приключение, фантастика, детектив, фэнтези, научная фантастика
- Референсные произведения используются для генерации стиля истории и обложки
- Структура: `{"genre_id": {"name": "...", "description": "...", "references": ["...", "..."]}}`

**Принципы:**
- Автоматическое приветствие для новых пользователей
- Простой пошаговый процесс создания истории
- Расширенный выбор жанров с примерами
- Интерактивное сочинение с чередованием ролей
- Полное управление историями (просмотр, удаление)
- Пользователь контролирует ключевые параметры
- Позитивная обратная связь на каждом этапе
- Фокус на творчестве и развитии ребенка

## 9. Деплой

**Варианты деплоя через Make:**

```makefile
# Локальная разработка/тестирование (без Docker)
make install        # uv sync - установка зависимостей
make init-db        # инициализация БД (создание таблиц из schema.sql)
make run            # uv run src/main.py - запуск бота
make test           # pytest - запуск тестов

# Локальная разработка с Docker
make docker-build   # docker build -t storytelling-bot .
make docker-run     # docker run с volume для data/
make docker-stop    # остановка контейнера
make docker-logs    # просмотр логов контейнера

# Деплой на облачный VPS (только Docker)
make docker-build   # docker build -t storytelling-bot .
make docker-deploy  # docker run -d --restart=always --env-file .env -v ./data:/app/data storytelling-bot
make docker-stop    # остановка и удаление контейнера
make docker-logs    # просмотр логов контейнера
```

**1. Локальная разработка без Docker:**

```bash
# Установка
make install

# Инициализация
make init-db
# Создать data/genres.json вручную
# Создать src/prompts/*.txt

# Запуск
make run
```

**2. Локальная разработка с Docker:**

```bash
# Сборка образа
make docker-build

# Запуск с volume
make docker-run  # монтирует ./data для сохранения БД и изображений

# Просмотр логов
make docker-logs
```

**3. Деплой на облачный VPS (только Docker):**

**Подготовка сервера:**
- Аренда облачного VPS (DigitalOcean, Hetzner, Selectel)
- Минимальные требования: 1GB RAM, 20GB диск, Ubuntu 22.04+
- Установка Docker и Docker Compose

**Процесс деплоя:**

1. **Настройка сервера:**
   ```bash
   # Клонирование репозитория
   git clone <repo> && cd llmstart_bot_homework
   
   # Создание .env файла с токенами
   cp .env.example .env
   nano .env
   ```

2. **Подготовка данных:**
   ```bash
   # Создание структуры папок
   mkdir -p data/images/uploads data/images/covers
   
   # Инициализация БД (выполнится при первом запуске контейнера)
   # Создание data/genres.json со справочником жанров
   # Создание промптов в src/prompts/
   ```

3. **Сборка и запуск:**
   ```bash
   make docker-build
   make docker-deploy
   ```

4. **Мониторинг:**
   ```bash
   make docker-logs  # просмотр логов
   docker ps         # статус контейнера
   ```

**Требования к серверу:**
- **Docker** обязателен для VPS
- 1GB RAM минимум (рекомендуется 2GB для Image Generation)
- 20GB диск (для образов Docker, БД и изображений)
- Постоянное интернет-соединение
- Открытый доступ к Telegram API и AI-сервисам

**Принципы:**
- VPS только через Docker (изоляция, простота деплоя)
- Локальная разработка: с Docker или без (на выбор разработчика)
- Docker volume для data/ (сохранение данных при перезапуске)
- `--restart=always` для автоматического перезапуска на VPS
- Максимальная автоматизация через Make команды
- Один контейнер, никаких сложных оркестраций

**Кроссплатформенность деплоя:**

*Makefile с автоопределением ОС:*
- Makefile автоматически определяет Windows или Linux/macOS
- Условные команды: PowerShell для Windows, bash для Linux/macOS
- Единый интерфейс команд (make install, make run, make test и т.д.)
- Volume paths: `$(CURDIR)` для Windows, `$(PWD)` для Linux
- Создание директорий через соответствующие команды ОС

*Управление фоновыми процессами (scripts/daemon.py):*
- Кроссплатформенный Python скрипт для управления ботом
- Windows: `subprocess` с флагом `DETACHED_PROCESS`, остановка через `taskkill`
- Linux: `nohup` + `os.setpgrp()`, остановка через сигналы SIGTERM/SIGKILL
- PID файл `.bot.pid` для отслеживания запущенного процесса
- Логи фонового процесса в `logs/bot.log`
- Команды: `make start` (фоновый запуск), `make stop`, `make restart`, `make status`

*Docker:*
- Одинаковый интерфейс на всех платформах (команды идентичны)
- Volume монтирование работает одинаково после настройки путей в Makefile
- Изоляция от платформо-зависимых особенностей ОС
- Рекомендуется для продакшена (VPS) для максимальной переносимости

## 10. Конфигурирование

**Конфигурация через `.env`:**

```bash
# .env файл
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# LLM (polza.ai или другой OpenAI-compatible сервис)
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.polza.ai/v1
LLM_MODEL=openai/gpt-4o-mini

# Speech-to-Text
SPEECH_API_KEY=your_speech_api_key
SPEECH_BASE_URL=https://api.openai.com/v1
SPEECH_MODEL=whisper-1

# Image Generation
IMAGE_GEN_API_KEY=your_image_gen_api_key
IMAGE_GEN_BASE_URL=https://api.openai.com/v1
IMAGE_GEN_MODEL=dall-e-3

# Vision
VISION_API_KEY=your_vision_api_key
VISION_BASE_URL=https://api.openai.com/v1
VISION_MODEL=gpt-4o-mini

# Database
DB_PATH=data/stories.db

# Хранение файлов
IMAGES_BASE_PATH=data/images
MAX_IMAGE_SIZE_MB=5

# Настройки историй (пары сообщений)
MAX_PAIRS_SHORT=5
MAX_PAIRS_MEDIUM=10
MAX_PAIRS_LONG=20

# Настройки креативности (температура LLM)
CREATIVITY_LOW=0.5
CREATIVITY_MEDIUM=0.7
CREATIVITY_HIGH=0.9

# Ограничения
MAX_MESSAGE_LENGTH=500

# Логирование
LOG_LEVEL=INFO
```

**Структура конфигурации в коде:**

```python
# config.py
from os import getenv
from dotenv import load_dotenv

load_dotenv()

config = {
    # Telegram
    "telegram_token": getenv("TELEGRAM_BOT_TOKEN"),
    
    # LLM
    "llm_api_key": getenv("LLM_API_KEY"),
    "llm_base_url": getenv("LLM_BASE_URL", "https://api.polza.ai/v1"),
    "llm_model": getenv("LLM_MODEL", "openai/gpt-4o-mini"),
    
    # Speech-to-Text
    "speech_api_key": getenv("SPEECH_API_KEY"),
    "speech_base_url": getenv("SPEECH_BASE_URL", "https://api.openai.com/v1"),
    "speech_model": getenv("SPEECH_MODEL", "whisper-1"),
    
    # Image Generation
    "image_gen_api_key": getenv("IMAGE_GEN_API_KEY"),
    "image_gen_base_url": getenv("IMAGE_GEN_BASE_URL", "https://api.openai.com/v1"),
    "image_gen_model": getenv("IMAGE_GEN_MODEL", "dall-e-3"),
    
    # Vision
    "vision_api_key": getenv("VISION_API_KEY"),
    "vision_base_url": getenv("VISION_BASE_URL", "https://api.openai.com/v1"),
    "vision_model": getenv("VISION_MODEL", "gpt-4o-mini"),
    
    # Database
    "db_path": getenv("DB_PATH", "data/stories.db"),
    
    # Хранение файлов
    "images_base_path": getenv("IMAGES_BASE_PATH", "data/images"),
    "max_image_size_mb": int(getenv("MAX_IMAGE_SIZE_MB", "5")),
    
    # Настройки историй
    "max_pairs_short": int(getenv("MAX_PAIRS_SHORT", "5")),
    "max_pairs_medium": int(getenv("MAX_PAIRS_MEDIUM", "10")),
    "max_pairs_long": int(getenv("MAX_PAIRS_LONG", "20")),
    
    # Настройки креативности
    "creativity_low": float(getenv("CREATIVITY_LOW", "0.5")),
    "creativity_medium": float(getenv("CREATIVITY_MEDIUM", "0.7")),
    "creativity_high": float(getenv("CREATIVITY_HIGH", "0.9")),
    
    # Ограничения
    "max_message_length": int(getenv("MAX_MESSAGE_LENGTH", "500")),
    
    # Логирование
    "log_level": getenv("LOG_LEVEL", "INFO"),
}
```

**Конфигурация справочника жанров:**

Файл `data/genres.json`:
```json
{
  "fairy_tale": {
    "name": "Сказка",
    "description": "Волшебные истории с добрыми и злыми героями",
    "references": ["Золушка", "Красная Шапочка", "Колобок"]
  },
  "adventure": {
    "name": "Приключение",
    "description": "Захватывающие путешествия и открытия",
    "references": ["Остров сокровищ", "Робинзон Крузо"]
  },
  "fantasy": {
    "name": "Фэнтези",
    "description": "Магия, драконы и необычные миры",
    "references": ["Гарри Поттер", "Хоббит"]
  },
  "detective": {
    "name": "Детектив",
    "description": "Расследования и разгадывание тайн",
    "references": ["Шерлок Холмс", "Эмиль и сыщики"]
  },
  "sci_fi": {
    "name": "Научная фантастика",
    "description": "Истории о будущем, космосе и технологиях",
    "references": ["Незнайка на Луне", "Маленький принц"]
  }
}
```

**Работа с секретными данными:**
- `.env` файл добавлен в `.gitignore` (НЕ попадает в git)
- `.env.example` с шаблоном (БЕЗ реальных ключей)
- В продакшне (VPS) используются реальные переменные окружения через `.env`
- Файлы с секретами имеют права доступа 600 (только владелец)
- Логирование НЕ выводит значения секретных переменных (API ключи)

**Принципы:**
- Все настройки через переменные окружения
- Значения по умолчанию для необязательных параметров
- Безопасность секретных данных
- Гибкость выбора AI-провайдеров (все через OpenAI-compatible API)
- Справочник жанров в отдельном файле для удобного редактирования
- Ограничение длины сообщений для контроля объема текста

## 11. Логирование

**Настройка логгера:**

```python
import logging

logging.basicConfig(
    level=config["log_level"],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()  # консоль для разработки
    ]
)

logger = logging.getLogger(__name__)
```

**Что логируем:**
- Запуск/остановка бота
- Входящие сообщения от пользователей (без полного содержимого)
- Команды пользователей (/start, /new_story, /my_stories)
- Создание, завершение и удаление историй
- Запросы к AI-сервисам (LLM, Speech, Vision, Image Gen)
- Ответы от AI-сервисов (длина, использование токенов)
- Ошибки и исключения с полным traceback
- Работа с БД (создание, обновление, удаление записей)

**Уровни логирования:**
- `INFO` - основные события (запуск, команды, создание историй, запросы к AI)
- `ERROR` - ошибки API, исключения, проблемы с БД
- `DEBUG` - детальная отладочная информация (содержимое запросов, детали обработки)

**Примеры логирования:**
```python
# При создании истории
logger.info(f"User {user_id} started new story: genre={genre}, duration={duration}")

# При запросе к LLM
logger.info(f"LLM request: model={model}, temp={temperature}, messages={len(messages)}")
logger.info(f"LLM response: length={len(response)}, tokens={tokens_used}")

# При ошибках
logger.error(f"Failed to generate image: {error}", exc_info=True)

# При работе с БД
logger.info(f"Story {story_id} completed and saved to database")
logger.info(f"Story {story_id} deleted by user {user_id}")
```

**Принципы:**
- Один лог-файл `logs/bot.log` (папка создается автоматически)
- В Docker логи также выводятся в stdout для `docker logs`
- Ротация логов НЕ требуется для MVP (можно добавить позже)
- Никаких секретных данных в логах (API ключи, токены маскируются)
- Логирование использования токенов для контроля расходов
- Простое текстовое форматирование с временными метками