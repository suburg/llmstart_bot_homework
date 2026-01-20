import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_prompt(filename: str) -> str:
    """
    Загрузить промпт из файла
    
    Args:
        filename: Имя файла промпта (например, "system.txt" или "cover_generation.txt")
    
    Returns:
        Содержимое промпта
    """
    prompt_path = Path(__file__).parent.parent / "prompts" / filename
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt {filename}: {e}")
        raise


def load_system_prompt() -> str:
    """Загрузить системный промпт из файла"""
    prompt = load_prompt("system.txt")
    logger.info(f"Loaded system prompt: {len(prompt)} chars")
    return prompt


def get_current_system_prompt(chat_id: int) -> str:
    """Получить текущий системный промпт (кастомный или дефолтный)"""
    from src.storage.memory import get_session
    
    session = get_session(chat_id)
    custom = session.get("custom_prompt")
    
    if custom:
        logger.info(f"Using custom prompt for chat_id: {chat_id}")
        return custom
    
    return load_system_prompt()
