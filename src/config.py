from os import getenv
from dotenv import load_dotenv

load_dotenv()

config = {
    "telegram_token": getenv("TELEGRAM_BOT_TOKEN"),
    "llm_api_key": getenv("LLM_API_KEY"),
    "llm_base_url": getenv("LLM_BASE_URL"),
    "llm_model": getenv("LLM_MODEL", "openai/gpt-4o-mini"),
    
    # Speech-to-Text API
    # Для polza.ai используйте: https://api.polza.ai/api/v1
    # Для OpenAI используйте: https://api.openai.com/v1
    "speech_api_key": getenv("SPEECH_API_KEY"),
    "speech_base_url": getenv("SPEECH_BASE_URL"),
    "speech_model": getenv("SPEECH_MODEL", "whisper-1"),
    
    # Image Generation API (polza.ai seedream-v4)
    "image_gen_api_key": getenv("IMAGE_GEN_API_KEY"),
    "image_gen_base_url": getenv("IMAGE_GEN_BASE_URL", "https://api.polza.ai/api/v1"),
    "image_gen_model": getenv("IMAGE_GEN_MODEL", "seedream-v4"),
    
    # База данных
    "db_path": getenv("DB_PATH", "data/stories.db"),
    
    # Хранение файлов
    "images_base_path": getenv("IMAGES_BASE_PATH", "data/images"),
    
    # Настройки историй (пары сообщений)
    "max_pairs_short": int(getenv("MAX_PAIRS_SHORT", "5")),
    "max_pairs_medium": int(getenv("MAX_PAIRS_MEDIUM", "10")),
    "max_pairs_long": int(getenv("MAX_PAIRS_LONG", "20")),
    
    # Настройки креативности (температура LLM)
    "creativity_low": float(getenv("CREATIVITY_LOW", "0.5")),
    "creativity_medium": float(getenv("CREATIVITY_MEDIUM", "0.7")),
    "creativity_high": float(getenv("CREATIVITY_HIGH", "0.9")),
    
    "log_level": getenv("LOG_LEVEL", "INFO"),
}

# Валидация критических настроек
if not config["telegram_token"]:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")
if not config["llm_api_key"]:
    raise ValueError("LLM_API_KEY must be set in environment variables")
if not config["llm_base_url"]:
    raise ValueError("LLM_BASE_URL must be set in environment variables")
if not config["speech_api_key"]:
    raise ValueError("SPEECH_API_KEY must be set in environment variables")