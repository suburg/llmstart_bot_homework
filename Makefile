.PHONY: install init-db run start stop status clean test docker-build docker-deploy docker-run docker-stop docker-logs

# Определение операционной системы
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    RM := powershell -Command Remove-Item -ErrorAction SilentlyContinue
    MKDIR := powershell -Command New-Item -ItemType Directory -Force
else
    DETECTED_OS := $(shell uname -s)
    RM := rm -f
    MKDIR := mkdir -p
endif

# Установка зависимостей через uv
install:
	uv sync --extra dev

# Инициализация базы данных
init-db:
	uv run python -c "from src.storage.database import init_database; init_database(); print('Database initialized successfully')"

# Запуск бота в текущем терминале (для разработки)
run:
	uv run python -m src.main

# Запуск бота в фоновом режиме
start:
	@echo "Starting bot in background..."
	@uv run python scripts/daemon.py start
	@echo "Bot started. PID saved to .bot.pid"

# Остановка бота
stop:
	@echo "Stopping bot..."
	@uv run python scripts/daemon.py stop

# Проверка статуса бота
status:
	@uv run python scripts/daemon.py status

# Очистка временных файлов
clean:
ifeq ($(DETECTED_OS),Windows)
	@powershell -Command "if (Test-Path logs/bot.log) { Remove-Item logs/bot.log }"
	@powershell -Command "Get-ChildItem -Path . -Recurse -Filter '__pycache__' -Directory | Remove-Item -Recurse -Force"
else
	@rm -f logs/bot.log
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
endif

# Запуск тестов
test:
	uv run pytest tests/ -v

# Docker: сборка образа
docker-build:
	docker build -t suburg-llmstart-bot .

# Docker: запуск контейнера (production)
docker-deploy:
	@echo "Creating data directories if needed..."
ifeq ($(DETECTED_OS),Windows)
	@powershell -Command "New-Item -ItemType Directory -Force -Path data/images/uploads, data/images/covers | Out-Null"
	@docker run -d --name suburg-llmstart-bot --restart=always --env-file .env -v $(CURDIR)/data:/app/data suburg-llmstart-bot
else
	@mkdir -p data/images/uploads data/images/covers
	@docker run -d --name suburg-llmstart-bot --restart=always --env-file .env -v $(PWD)/data:/app/data suburg-llmstart-bot
endif

# Docker: запуск контейнера (для разработки, без detached)
docker-run:
	@echo "Creating data directories if needed..."
ifeq ($(DETECTED_OS),Windows)
	@powershell -Command "New-Item -ItemType Directory -Force -Path data/images/uploads, data/images/covers | Out-Null"
	@docker run --rm --name suburg-llmstart-bot --env-file .env -v $(CURDIR)/data:/app/data suburg-llmstart-bot
else
	@mkdir -p data/images/uploads data/images/covers
	@docker run --rm --name suburg-llmstart-bot --env-file .env -v $(PWD)/data:/app/data suburg-llmstart-bot
endif

# Docker: остановка и удаление контейнера
docker-stop:
	docker stop suburg-llmstart-bot || true
	docker rm suburg-llmstart-bot || true

# Docker: просмотр логов
docker-logs:
	docker logs -f suburg-llmstart-bot