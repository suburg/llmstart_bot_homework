.PHONY: install run start stop status clean

# Установка зависимостей через uv
install:
	uv sync

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