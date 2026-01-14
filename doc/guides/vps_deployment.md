# Развертывание бота на облачном VPS

Пошаговая инструкция по развертыванию Telegram бота на виртуальном сервере (VPS) с использованием Docker.

## Предварительные требования

- VPS на beget.com с Ubuntu Linux (20.04 или новее)
- Доступ к серверу по SSH
- Telegram Bot Token
- OpenRouter API Key
- GitHub репозиторий с кодом бота

## 1. Настройка SSH доступа

### 1.1. Создание SSH ключа (на локальной машине)

Если у вас еще нет SSH ключа:

**Для Linux/Mac:**

```bash
# Генерация SSH ключа
ssh-keygen -t ed25519 -C "your_email@example.com"

# Вывести публичный ключ для копирования
cat ~/.ssh/id_ed25519.pub
```

**Для Windows (PowerShell или CMD):**

```powershell
# Генерация SSH ключа
ssh-keygen -t ed25519 -C "your_email@example.com"

# Вывести публичный ключ для копирования
type %USERPROFILE%\.ssh\id_ed25519.pub

# ИЛИ в PowerShell:
# Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

**Альтернатива для Windows:** Используйте [PuTTYgen](https://www.putty.org/) для генерации ключей через графический интерфейс.

### 1.2. Добавление публичного ключа на сервер

Скопируйте содержимое публичного ключа и добавьте его на сервер через панель управления beget.com или выполните на сервере:

```bash
# На сервере (если есть доступ по паролю)
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Вставить публичный ключ и сохранить (Ctrl+X, Y, Enter)
chmod 600 ~/.ssh/authorized_keys
```

### 1.3. Подключение к серверу

```bash
# Подключение по SSH
ssh username@your-vps-ip

# Пример:
# ssh user@185.123.45.67
```

## 2. Базовая настройка безопасности сервера

### 2.1. Обновление системы

```bash
# Обновление списка пакетов
sudo apt update

# Обновление установленных пакетов
sudo apt upgrade -y
```

### 2.2. Настройка файрвола (UFW)

```bash
# Установка UFW (если не установлен)
sudo apt install ufw -y

# Разрешить SSH (ВАЖНО! Сделать до включения файрвола)
sudo ufw allow 22/tcp

# Включить файрвол
sudo ufw enable

# Проверить статус
sudo ufw status
```

## 3. Установка Docker

### 3.1. Проверка наличия Docker

Сначала проверьте, не установлен ли Docker уже на сервере:

```bash
# Проверка установленной версии Docker
docker --version

# Если команда выполнилась успешно, Docker уже установлен
# Можете пропустить шаги 3.2-3.5 и перейти к разделу 4
```

Если получили ошибку "command not found", продолжайте установку.

### 3.2. Установка зависимостей

```bash
# Установка необходимых пакетов
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### 3.3. Добавление официального GPG ключа Docker

```bash
# Создание директории для ключей
sudo install -m 0755 -d /etc/apt/keyrings

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### 3.4. Добавление репозитория Docker

```bash
# Добавление репозитория
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 3.5. Установка Docker Engine

```bash
# Обновление индекса пакетов
sudo apt update

# Установка Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Проверка установки
sudo docker --version
```

### 3.6. Настройка прав пользователя для Docker

```bash
# Добавление текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Применение изменений (нужно переподключиться или выполнить)
newgrp docker

# Проверка работы без sudo
docker ps
```

## 4. Клонирование репозитория

### 4.1. Установка Git (если не установлен)

```bash
sudo apt install git -y
```

### 4.2. Клонирование проекта

```bash
# Переход в домашнюю директорию
cd ~

# Клонирование репозитория
git clone https://github.com/YOUR_USERNAME/llmstart_bot_homework.git

# Переход в директорию проекта
cd llmstart_bot_homework
```

**Примечание:** Замените `YOUR_USERNAME` на ваше имя пользователя GitHub.

Если репозиторий приватный, используйте Personal Access Token:

```bash
# Для приватного репозитория
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/llmstart_bot_homework.git
```

## 5. Настройка переменных окружения

### 5.1. Создание .env файла

```bash
# Создание .env файла на основе примера (если есть .env.example)
cp .env.example .env

# ИЛИ создание нового .env файла
nano .env
```

### 5.2. Содержимое .env файла

Добавьте следующие переменные:

```env
# Telegram Bot Token (получен от @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# LLM API Key
LLM_API_KEY=your_llm_api_key_here

# LLM Model (опционально)
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Максимальная длина истории сообщений
MAX_HISTORY_LENGTH=10
```

Сохраните файл (Ctrl+X, Y, Enter).

### 5.3. Проверка .env файла

```bash
# Просмотр содержимого (убедитесь, что токены на месте)
cat .env
```

## 6. Сборка и запуск Docker контейнера

Проект включает `Makefile` с готовыми командами для работы с Docker. Вы можете использовать их для упрощения процесса.

### 6.1. Установка Make (если не установлен)

```bash
# Проверка наличия Make
make --version

# Если не установлен, установите:
sudo apt install make -y
```

### 6.2. Сборка Docker образа

**Вариант A: Используя Makefile (рекомендуется)**

```bash
# Сборка образа через Makefile
make docker-build

# Эта команда выполняет: docker build -t telegram-bot .
```

**Вариант B: Прямой вызов Docker**

```bash
# Сборка образа напрямую
docker build -t telegram-bot .

# Проверка созданного образа
docker images | grep telegram-bot
```

### 6.3. Запуск контейнера с автоперезапуском

**Вариант A: Используя Makefile (рекомендуется)**

```bash
# Запуск контейнера через Makefile
make docker-deploy

# Эта команда автоматически:
# - Запускает контейнер с именем telegram-bot
# - Настраивает автоперезапуск
# - Монтирует директорию логов
# - Загружает переменные из .env
```

**Вариант B: Прямой вызов Docker**

```bash
# Запуск контейнера с политикой автоперезапуска
docker run -d \
  --name telegram-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  telegram-bot

# Проверка статуса контейнера
docker ps
```

**Параметры запуска:**
- `-d` - запуск в фоновом режиме (detached)
- `--name telegram-bot` - имя контейнера
- `--restart unless-stopped` - автоматический перезапуск при сбое или перезагрузке сервера
- `--env-file .env` - загрузка переменных окружения из файла
- `-v $(pwd)/logs:/app/logs` - монтирование директории логов

### 6.4. Проверка логов

**Используя Makefile:**

```bash
# Просмотр логов через Makefile
make docker-logs
```

**Используя Docker напрямую:**

```bash
# Просмотр логов контейнера
docker logs telegram-bot

# Просмотр логов в реальном времени
docker logs -f telegram-bot

# Последние 100 строк логов
docker logs --tail 100 telegram-bot
```

## 7. Управление контейнером

### 7.1. Основные команды

**Используя Makefile:**

```bash
# Остановка контейнера
make docker-stop

# Просмотр логов
make docker-logs

# Просмотр статуса (через docker ps)
docker ps | grep telegram-bot
```

**Используя Docker напрямую:**

```bash
# Просмотр запущенных контейнеров
docker ps

# Остановка контейнера
docker stop telegram-bot

# Запуск остановленного контейнера
docker start telegram-bot

# Перезапуск контейнера
docker restart telegram-bot

# Удаление контейнера (сначала нужно остановить)
docker stop telegram-bot
docker rm telegram-bot
```

### 7.2. Обновление бота

При обновлении кода в репозитории:

**Вариант A: Используя Makefile**

```bash
# 1. Переход в директорию проекта
cd ~/llmstart_bot_homework

# 2. Остановка контейнера
make docker-stop

# 3. Обновление кода из репозитория
git pull origin main

# 4. Пересборка образа
make docker-build

# 5. Запуск нового контейнера
make docker-deploy
```

**Вариант B: Используя Docker напрямую**

```bash
# 1. Переход в директорию проекта
cd ~/llmstart_bot_homework

# 2. Остановка и удаление старого контейнера
docker stop telegram-bot
docker rm telegram-bot

# 3. Обновление кода из репозитория
git pull origin main

# 4. Пересборка образа
docker build -t telegram-bot .

# 5. Запуск нового контейнера
docker run -d \
  --name telegram-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  telegram-bot
```

### 7.3. Просмотр использования ресурсов

```bash
# Статистика использования ресурсов контейнером
docker stats telegram-bot

# Нажмите Ctrl+C для выхода
```

## 8. Мониторинг и обслуживание

### 8.1. Проверка работоспособности

```bash
# Проверка статуса контейнера
docker ps | grep telegram-bot

# Проверка последних логов
docker logs --tail 50 telegram-bot

# Проверка файла логов на сервере
tail -f logs/bot.log
```

### 8.2. Очистка неиспользуемых ресурсов Docker

```bash
# Удаление остановленных контейнеров, неиспользуемых образов и сетей
docker system prune -a

# С подтверждением удаления volumes
docker system prune -a --volumes
```

### 8.3. Резервное копирование логов

```bash
# Создание архива логов
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Просмотр созданных архивов
ls -lh logs-backup-*.tar.gz
```

## 9. Troubleshooting

### 9.1. Контейнер не запускается

```bash
# Проверка логов для диагностики
docker logs telegram-bot

# Запуск контейнера в интерактивном режиме для отладки
docker run -it --rm --env-file .env telegram-bot bash
```

### 9.2. Бот не отвечает в Telegram

1. Проверьте логи контейнера:
```bash
docker logs telegram-bot
```

2. Проверьте переменные окружения:
```bash
docker exec telegram-bot env | grep TELEGRAM
docker exec telegram-bot env | grep LLM
```

3. Проверьте сетевое подключение:
```bash
docker exec telegram-bot ping -c 3 8.8.8.8
```

### 9.3. Ошибки с правами доступа к логам

```bash
# Изменение владельца директории логов
sudo chown -R $USER:$USER logs/

# Изменение прав доступа
chmod -R 755 logs/
```

### 9.4. Недостаточно места на диске

```bash
# Проверка использования диска
df -h

# Очистка старых Docker образов и контейнеров
docker system prune -a

# Очистка старых логов (осторожно!)
rm -f logs/*.log.old
```

### 9.5. Ошибка "port already in use"

Этот бот не использует порты, но если возникает конфликт имен:

```bash
# Проверка существующих контейнеров с таким именем
docker ps -a | grep telegram-bot

# Удаление конфликтующего контейнера
docker rm -f telegram-bot
```

## 10. Безопасность

### 10.1. Защита .env файла

```bash
# Установка правильных прав доступа
chmod 600 .env

# Проверка
ls -la .env
```

### 10.2. Регулярное обновление системы

```bash
# Создание скрипта для автоматического обновления
sudo nano /etc/cron.weekly/system-update

# Содержимое скрипта:
#!/bin/bash
apt update && apt upgrade -y
apt autoremove -y

# Сделать скрипт исполняемым
sudo chmod +x /etc/cron.weekly/system-update
```

### 10.3. Настройка fail2ban (опционально)

```bash
# Установка fail2ban для защиты от брутфорса SSH
sudo apt install fail2ban -y

# Запуск и включение автозапуска
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

## 11. Полезные команды

```bash
# Просмотр всех Docker образов
docker images

# Просмотр всех контейнеров (включая остановленные)
docker ps -a

# Вход в работающий контейнер
docker exec -it telegram-bot bash

# Копирование файла из контейнера
docker cp telegram-bot:/app/logs/bot.log ./bot.log

# Просмотр информации о контейнере
docker inspect telegram-bot

# Просмотр использования диска Docker
docker system df
```

## Заключение

После выполнения всех шагов ваш Telegram бот будет:
- ✅ Работать на VPS в Docker контейнере
- ✅ Автоматически перезапускаться при сбоях
- ✅ Запускаться при перезагрузке сервера
- ✅ Логировать свою работу
- ✅ Быть защищенным базовыми настройками безопасности

Для проверки работоспособности откройте Telegram и отправьте команду `/start` вашему боту.
