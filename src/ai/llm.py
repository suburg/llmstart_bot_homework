import logging
from openai import AsyncOpenAI

from src.config import config

logger = logging.getLogger(__name__)

def create_llm_client() -> AsyncOpenAI:
    """Создание клиента для OpenRouter"""
    return AsyncOpenAI(
        base_url=config["llm_base_url"],
        api_key=config["llm_api_key"],
    )

async def send_message(
    messages: list[dict[str, str]], 
    model: str | None = None,
    temperature: float = 0.7
) -> str:
    """
    Отправка сообщения в LLM
    
    Args:
        messages: Список сообщений в формате OpenAI API
        model: Модель для использования (если не указана - из config)
        temperature: Температура генерации (креативность)
    
    Returns:
        Ответ от LLM
    """
    if model is None:
        model = config["llm_model"]
    
    client = create_llm_client()
    
    try:
        logger.info(
            f"LLM Request: model={model}, temp={temperature}, "
            f"messages_count={len(messages)}"
        )
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        
        answer = response.choices[0].message.content
        logger.info(f"LLM Response: length={len(answer)} chars")
        
        return answer
        
    except Exception as e:
        logger.error(f"LLM Error: {type(e).__name__}: {e}")
        raise
