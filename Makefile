.PHONY: install run clean

# Установка зависимостей через uv
install:
	uv sync

# Запуск бота
run:
	uv run src/main.py

# Очистка временных файлов
clean:
	rm -f bot.log
	find . -type d -name "__pycache__" -exec rm -rf {} +