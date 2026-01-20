# Обновления Docker и Makefile для работы с БД и изображениями

## 🔍 Обнаруженные проблемы

### Dockerfile
1. ❌ Не создавались директории для БД и изображений
2. ❌ Не копировался `data/genres.json` (критично для работы)
3. ❌ Не был объявлен VOLUME для персистентности данных

### Makefile - docker-deploy
1. ❌ Не монтировался volume для `data/` (БД терялась при перезапуске)
2. ❌ Не создавались локальные директории автоматически

## ✅ Внесенные изменения

### Dockerfile

**Добавлено:**
```dockerfile
# Создание директорий для логов, БД и изображений
RUN mkdir -p logs data/images/uploads data/images/covers

# Копирование справочника жанров (необходим для работы бота)
COPY data/genres.json ./data/

# Volume для персистентности данных (БД, изображения)
VOLUME ["/app/data"]
```

**Что это даёт:**
- ✅ Автоматическое создание всех необходимых директорий
- ✅ `genres.json` включается в образ и доступен боту
- ✅ Объявленный VOLUME обеспечивает сохранность данных

### Makefile

**Обновлена команда docker-deploy:**
```makefile
docker-deploy:
	@echo "Creating data directories if needed..."
	@powershell -Command "New-Item -ItemType Directory -Force -Path data\images\uploads, data\images\covers | Out-Null"
	@echo "Starting container with volume mount..."
	docker run -d --name suburg-llmstart-bot --restart=always --env-file .env -v ${CURDIR}/data:/app/data suburg-llmstart-bot
```

**Добавлена новая команда docker-run:**
```makefile
docker-run:
	@echo "Creating data directories if needed..."
	@powershell -Command "New-Item -ItemType Directory -Force -Path data\images\uploads, data\images\covers | Out-Null"
	@echo "Starting container in foreground mode..."
	docker run --rm --name suburg-llmstart-bot --env-file .env -v ${CURDIR}/data:/app/data suburg-llmstart-bot
```

**Что это даёт:**
- ✅ Автоматическое создание директорий перед запуском
- ✅ Монтирование volume `-v ${CURDIR}/data:/app/data` для персистентности
- ✅ `--restart=always` для автоматического перезапуска на production
- ✅ `docker-run` для удобной разработки (foreground mode, auto-remove)

### README.md

Обновлены инструкции по Docker с пояснениями:
- Описание двух режимов запуска (production/development)
- Информация о автоматическом создании директорий
- Пояснение про volume и genres.json

## 🎯 Результат

### Что работает теперь:
1. ✅ **Персистентность БД** - `data/stories.db` сохраняется между перезапусками контейнера
2. ✅ **Сохранность изображений** - загруженные и сгенерированные изображения не теряются
3. ✅ **Автоматическая инициализация** - все необходимые директории создаются автоматически
4. ✅ **Справочник жанров** - `genres.json` доступен боту внутри контейнера
5. ✅ **Auto-restart** - контейнер перезапускается автоматически при сбоях (production)

### Структура volume:
```
./data/                          <- монтируется в /app/data внутри контейнера
├── stories.db                   <- БД с историями (персистентная)
├── genres.json                  <- копируется из образа при первом запуске
└── images/
    ├── uploads/                 <- загруженные пользователями изображения
    └── covers/                  <- сгенерированные обложки
```

## 📝 Команды для использования

### Локальная разработка (без Docker):
```bash
make install
make init-db
make run
```

### Docker (production):
```bash
make docker-build
make docker-deploy    # detached mode, auto-restart
make docker-logs      # просмотр логов
make docker-stop      # остановка
```

### Docker (разработка):
```bash
make docker-build
make docker-run       # foreground mode, auto-remove
# Ctrl+C для остановки
```

## ⚠️ Важно

1. **Volume монтируется из хоста** - данные в `./data/` на хосте будут видны в контейнере
2. **При удалении контейнера** данные в `./data/` на хосте сохраняются
3. **При пересборке образа** данные в volume не затрагиваются
4. **`genres.json` должен существовать** на хосте перед сборкой образа
