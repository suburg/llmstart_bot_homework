FROM python:3.14-slim

WORKDIR /app

# Установка uv
RUN pip install --no-cache-dir uv

# Копирование файлов проекта
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Установка зависимостей через uv
RUN uv sync --frozen

# Создание директории для логов
RUN mkdir -p logs

# Запуск бота
CMD ["uv", "run", "src/main.py"]
