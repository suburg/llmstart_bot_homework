from os import getenv
from dotenv import load_dotenv

load_dotenv()

config = {
    "telegram_token": getenv("TELEGRAM_BOT_TOKEN"),
    "llm_api_key": getenv("LLM_API_KEY"),
    "llm_base_url": getenv("LLM_BASE_URL"),
    "llm_model": getenv("LLM_MODEL", "openai/gpt-4o-mini"),
    "max_history_messages": int(getenv("MAX_HISTORY_MESSAGES", "10")),
    "log_level": getenv("LOG_LEVEL", "INFO"),
}

# Валидация критических настроек
if not config["telegram_token"]:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")
if not config["llm_api_key"]:
    raise ValueError("LLM_API_KEY must be set in environment variables")
if not config["llm_base_url"]:
    raise ValueError("LLM_BASE_URL must be set in environment variables")