from os import getenv
from dotenv import load_dotenv

load_dotenv()

config = {
    "telegram_token": getenv("TELEGRAM_BOT_TOKEN"),
    "log_level": getenv("LOG_LEVEL", "INFO"),
}

# Валидация критических настроек
if not config["telegram_token"]:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")