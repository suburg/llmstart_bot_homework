FROM python:3.14-slim

WORKDIR /app

# Установка uv
RUN pip install --no-cache-dir uv

# Копирование файлов проекта
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Установка зависимостей через uv
RUN uv sync --frozen

# Создание директорий для логов, БД и изображений
RUN mkdir -p logs data/images/uploads data/images/covers

# Копирование справочника жанров (необходим для работы бота)
COPY data/genres.json ./data/

# Volume для персистентности данных (БД, изображения)
VOLUME ["/app/data"]

# Запуск бота
CMD ["uv", "run", "python", "-m", "src.main"]
