-- Схема базы данных для хранения историй

CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- Telegram user ID (chat_id)
    title TEXT,                                   -- Название истории (генерируется после завершения)
    genre TEXT NOT NULL,                          -- Жанр истории
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
    initial_image_url TEXT,                       -- Относительный путь к загруженному изображению
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- Дата и время создания истории
    completed_at TIMESTAMP                        -- Дата и время завершения истории
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_stories_user_id ON stories(user_id);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
