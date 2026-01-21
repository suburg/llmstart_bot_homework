"""Модуль для проверки безопасности контента"""
import logging
import json
from src.ai.llm import send_message

logger = logging.getLogger(__name__)


async def check_content_safety(text: str) -> dict:
    """
    Проверка контента через LLM с промптом модерации
    
    Фильтрует только откровенный сексуальный контент
    
    Args:
        text: Текст для проверки
    
    Returns:
        dict: {"is_safe": bool, "reason": str}
    """
    moderation_prompt = """Ты - система модерации контента для детского приложения по сочинению историй.

Проанализируй следующий текст и определи, содержит ли он ОТКРОВЕННЫЙ СЕКСУАЛЬНЫЙ КОНТЕНТ или намеки сексуального характера.

ВАЖНО:
- Это приложение для детей
- Фильтруй ТОЛЬКО откровенный сексуальный контент
- НЕ блокируй обычные детективные сюжеты, приключения, фэнтези с элементами конфликта
- Романтика (поцелуи, любовь) БЕЗ сексуального подтекста - допустима

Ответь ТОЛЬКО в формате JSON:
{"is_safe": true/false, "reason": "краткое объяснение если небезопасно"}

Текст для проверки:"""
    
    try:
        messages = [
            {"role": "system", "content": moderation_prompt},
            {"role": "user", "content": text}
        ]
        
        response = await send_message(messages, temperature=0.0)
        
        # Парсим JSON ответ
        result = json.loads(response)
        
        if not result.get("is_safe", True):
            logger.warning(
                f"Content moderation flag: length={len(text)}, "
                f"reason={result.get('reason', 'unknown')}"
            )
        
        return {
            "is_safe": result.get("is_safe", True),
            "reason": result.get("reason", "")
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Moderation response JSON parse error: {e}, response: {response}")
        # При ошибке парсинга считаем контент безопасным
        return {"is_safe": True, "reason": ""}
    except Exception as e:
        logger.error(f"Moderation check error: {e}", exc_info=True)
        # При ошибке API считаем контент безопасным (fail-open для UX)
        return {"is_safe": True, "reason": ""}
