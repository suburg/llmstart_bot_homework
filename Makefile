.PHONY: install init-db run start stop status clean test docker-build docker-deploy docker-run docker-stop docker-logs

# Установка зависимостей через uv
install:
	uv sync

# Инициализация базы данных
init-db:
	uv run python -c "from src.storage.database import init_database; init_database(); print('Database initialized successfully')"

# Запуск бота в текущем терминале (для разработки)
run:
	uv run src/main.py

# Запуск бота в фоновом режиме
start:
	@echo "Starting bot in background..."
	@powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"uv run src/main.py\"' -WindowStyle Hidden -PassThru | Select-Object -ExpandProperty Id | Out-File -FilePath .bot.pid -Encoding ASCII"
	@echo "Bot started. PID saved to .bot.pid"

# Остановка бота
stop:
	@echo "Stopping bot..."
	@powershell -Command "if (Test-Path .bot.pid) { $$pid = Get-Content .bot.pid; Stop-Process -Id $$pid -Force -ErrorAction SilentlyContinue; Remove-Item .bot.pid -ErrorAction SilentlyContinue; Write-Host 'Bot stopped' } else { Write-Host 'Bot is not running (.bot.pid not found)' }"

# Проверка статуса бота
status:
	@powershell -Command "if (Test-Path .bot.pid) { $$pid = Get-Content .bot.pid; if (Get-Process -Id $$pid -ErrorAction SilentlyContinue) { Write-Host 'Bot is running (PID: '$$pid')' } else { Write-Host 'Bot is not running (stale PID file)'; Remove-Item .bot.pid } } else { Write-Host 'Bot is not running' }"

# Очистка временных файлов
clean:
	@powershell -Command "if (Test-Path logs/bot.log) { Remove-Item logs/bot.log }"
	@powershell -Command "Get-ChildItem -Path . -Recurse -Filter '__pycache__' -Directory | Remove-Item -Recurse -Force"

# Запуск тестов
test:
	uv run pytest tests/ -v

# Docker: сборка образа
docker-build:
	docker build -t suburg-llmstart-bot .

# Docker: запуск контейнера (production)
docker-deploy:
	@echo "Creating data directories if needed..."
	@powershell -Command "New-Item -ItemType Directory -Force -Path data\images\uploads, data\images\covers | Out-Null"
	@echo "Starting container with volume mount..."
	docker run -d --name suburg-llmstart-bot --restart=always --env-file .env -v ${CURDIR}/data:/app/data suburg-llmstart-bot

# Docker: запуск контейнера (для разработки, без detached)
docker-run:
	@echo "Creating data directories if needed..."
	@powershell -Command "New-Item -ItemType Directory -Force -Path data\images\uploads, data\images\covers | Out-Null"
	@echo "Starting container in foreground mode..."
	docker run --rm --name suburg-llmstart-bot --env-file .env -v ${CURDIR}/data:/app/data suburg-llmstart-bot

# Docker: остановка и удаление контейнера
docker-stop:
	docker stop suburg-llmstart-bot || true
	docker rm suburg-llmstart-bot || true

# Docker: просмотр логов
docker-logs:
	docker logs -f suburg-llmstart-bot