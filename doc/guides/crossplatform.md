# Изменения: Кроссплатформенная поддержка

## Дата: 22 января 2026

## Проблема
Makefile использовал PowerShell команды, которые не работали на Ubuntu Linux VPS. Это препятствовало развертыванию бота на серверах с Linux.

## Решение

### 1. Обновленный Makefile
- **Автоопределение ОС**: Добавлено определение операционной системы через переменные `OS` и `DETECTED_OS`
- **Условные команды**: Используются разные команды для Windows и Linux:
  - `clean`: PowerShell `Remove-Item` на Windows, `rm`/`find` на Linux
  - `docker-deploy/docker-run`: PowerShell `New-Item` на Windows, `mkdir -p` на Linux
  - Volume paths: `$(CURDIR)` на Windows, `$(PWD)` на Linux
- **Python для управления процессами**: Команды `start`, `stop`, `status` теперь используют Python скрипт

### 2. Новый скрипт scripts/daemon.py
Кроссплатформенный Python скрипт для управления ботом в фоновом режиме:

#### Windows
- Использует `subprocess.Popen` с флагами `CREATE_NEW_PROCESS_GROUP` и `DETACHED_PROCESS`
- Останавливает процесс через `taskkill /F /PID`
- Проверяет статус через `tasklist /FI "PID eq {pid}"`

#### Linux
- Использует `nohup` и `os.setpgrp()` для создания отдельной группы процессов
- Останавливает через сигналы `SIGTERM` и `SIGKILL`
- Проверяет статус через `os.kill(pid, 0)`

#### Функции
- `start_bot()` - запуск бота в фоне с сохранением PID в `.bot.pid`
- `stop_bot()` - graceful остановка с удалением PID файла
- `check_status()` - проверка запущенного процесса

### 3. Обновленная документация
- **README.md**: Добавлена информация о кроссплатформенности и командах управления
- **doc/conventions.md**: Добавлена секция "Кроссплатформенность" с рекомендациями

## Использование

### Локальная разработка (Windows)
```powershell
make install      # Установка зависимостей
make init-db      # Инициализация БД
make run          # Запуск в текущем терминале
make start        # Запуск в фоне
make status       # Проверка статуса
make stop         # Остановка
```

### Деплой на VPS (Ubuntu Linux)
```bash
make install      # Установка зависимостей
make init-db      # Инициализация БД
make run          # Запуск в текущем терминале
make start        # Запуск в фоне
make status       # Проверка статуса
make stop         # Остановка
```

### Docker (любая ОС)
```bash
make docker-build   # Сборка образа
make docker-deploy  # Запуск в production режиме
make docker-logs    # Просмотр логов
make docker-stop    # Остановка
```

## Тестирование

### На Windows
```powershell
# Проверка определения ОС
make clean

# Проверка управления процессами
make start
make status
make stop
```

### На Linux
```bash
# Проверка определения ОС
make clean

# Проверка управления процессами
make start
make status
make stop
```

## Технические детали

### Makefile переменные
- `OS=Windows_NT` - автоматически устанавливается на Windows
- `DETECTED_OS` - определяется через `uname -s` на Linux/macOS
- Условные блоки `ifeq ($(DETECTED_OS),Windows)` для платформо-зависимых команд

### PID файл и логи
- `.bot.pid` - хранит PID процесса бота (добавлен в `.gitignore`)
- `logs/bot.log` - вывод бота в фоновом режиме

## Совместимость
- ✅ Windows 10/11 (PowerShell)
- ✅ Ubuntu Linux 20.04+ (bash)
- ✅ macOS (bash/zsh)
- ✅ Docker (все платформы)

## Что НЕ изменилось
- Код бота и его функциональность
- Структура проекта
- Docker образ и контейнеризация
- API и конфигурация
