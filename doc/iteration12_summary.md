# Итерация 12: База данных для хранения историй

## ✅ Что реализовано

### Основной функционал
1. **SQLite база данных** для постоянного хранения историй
2. **Автоматическое сохранение** прогресса после каждого сообщения
3. **Восстановление активных историй** при перезапуске бота
4. **Команда `/my_stories`** для просмотра всех сохраненных историй
5. **Просмотр историй** из списка (завершенных, заброшенных, активных)

### Логика работы

#### Статусы историй:
- **`in_progress`** - активная история (только одна на пользователя, можно продолжить)
- **`completed`** - завершенная история (только чтение)
- **`abandoned`** - заброшенная история (только чтение)

#### Автоматический abandon:
При создании новой истории через `/new_story`:
1. Проверяется наличие активной истории
2. Если есть - автоматически помечается как `abandoned`
3. Пользователь получает уведомление: "⚠️ Твоя незавершённая история сохранена. Её можно найти в /my_stories"
4. Создается новая активная история

## 📁 Созданные файлы

### 1. `src/storage/schema.sql`
DDL-схема для создания таблицы `stories` с полями:
- id, user_id, title, genre, duration
- main_hero, additional_heroes, who_starts, creativity_level
- status, content (JSON), final_text
- cover_url, praise_text, initial_image_url
- created_at, completed_at

### 2. `src/storage/database.py`
CRUD операции с SQLite:
- `init_database()` - инициализация БД из schema.sql
- `create_story()` - создание новой истории
- `update_story_content()` - обновление контента
- `complete_story()` - завершение истории
- `abandon_story()` - пометка как заброшенной
- `get_active_story()` - получение активной истории пользователя
- `get_user_stories()` - все истории пользователя
- `get_story_by_id()` - конкретная история по ID
- `get_all_active_stories()` - все активные истории (для восстановления)

### 3. `src/storage/models.py`
Функция `create_story_dict()` для создания структуры новой истории

### 4. `tests/test_database.py`
8 тестов для проверки работы БД

## 🔧 Измененные файлы

### 1. `src/config.py`
Добавлен параметр: `"db_path": getenv("DB_PATH", "data/stories.db")`

### 2. `src/storage/memory.py`
- Добавлено поле `story_id` в сессию для связи с БД

### 3. `src/story/manager.py`
- `start_story_creation()` теперь проверяет активную историю и делает abandon
- `process_who_starts()` создает историю в БД после выбора всех параметров

### 4. `src/bot/handlers/commands.py`
- Обновлен обработчик `/new_story` для обработки abandon
- Добавлена команда `/my_stories` с просмотром списка историй
- Добавлен callback `view_story:` для просмотра конкретной истории
- Добавлено сохранение в БД при начале истории от бота и продолжении

### 5. `src/bot/handlers/messages.py`
- Добавлено сохранение в БД после каждого сообщения пользователя
- Добавлено сохранение в БД после каждого ответа бота
- Передача `story_id` в `finalize_story()`

### 6. `src/story/formatter.py`
- `finalize_story()` теперь принимает `story_id` и сохраняет результат в БД

### 7. `src/main.py`
- Добавлена функция `restore_active_stories()` для восстановления при старте
- Автоматическая инициализация БД при старте

### 8. `Makefile`
Добавлена команда: `make init-db` для ручной инициализации БД

### 9. `.env.example` (обновлен)
Добавлен параметр: `DB_PATH=data/stories.db`

## 🧪 Тестирование

Все тесты пройдены: **15/15** ✅

- 7 старых тестов (работа с сессиями)
- 8 новых тестов (работа с БД)

```bash
make test
```

## 🚀 Использование

### Первый запуск
```bash
# 1. Установить зависимости
make install

# 2. Инициализировать БД (опционально, выполнится автоматически)
make init-db

# 3. Запустить бота
make run
```

### Команды бота
- `/start` - приветствие
- `/new_story` - создать новую историю (старая станет abandoned)
- `/my_stories` - посмотреть все свои истории
- `/help` - справка

### Как это работает
1. Пользователь создает историю через `/new_story`
2. После выбора всех параметров история сохраняется в БД с status='in_progress'
3. Каждое сообщение сохраняется в БД (поле `content` как JSON)
4. При завершении история получает status='completed', title и final_text
5. При создании новой истории старая активная получает status='abandoned'
6. При перезапуске бота все активные истории восстанавливаются в память

## 📊 Структура данных

### Таблица stories
```sql
CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    genre TEXT NOT NULL,
    duration TEXT NOT NULL CHECK(...),
    main_hero TEXT NOT NULL,
    additional_heroes TEXT,
    who_starts TEXT NOT NULL CHECK(...),
    creativity_level TEXT NOT NULL CHECK(...),
    status TEXT NOT NULL CHECK(...),
    content TEXT,  -- JSON: [{"role": "user", "content": "..."}, ...]
    final_text TEXT,
    cover_url TEXT,
    praise_text TEXT,
    initial_image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

## 🎯 Что дальше

Следующая итерация: **Итерация 13 - Генерация персональной похвалы**
