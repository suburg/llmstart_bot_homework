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


async def generate_praise(content: list, params: dict) -> str:
    """
    Генерация персональной похвалы для ребенка
    
    Анализирует вклад пользователя и выделяет лучшие идеи
    
    Args:
        content: Массив сообщений истории
        params: Параметры истории (жанр, герои)
    
    Returns:
        Текст похвалы
    """
    from pathlib import Path
    
    user_messages = [
        msg["content"] for msg in content if msg["role"] == "user"
    ]
    
    if not user_messages:
        return "Отличная работа! Ты создал замечательную историю! 🎉"
    
    prompt_path = Path(__file__).parent.parent / "prompts" / "praise.txt"
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            praise_prompt = f.read().strip()
    except FileNotFoundError:
        logger.error(f"Praise prompt not found: {prompt_path}")
        praise_prompt = (
            "Ты добрый наставник. Похвали ребенка за вклад в историю. "
            "Выдели 1-2 лучшие идеи. Будь конкретным и искренним."
        )
    
    user_text = "\n\n".join(user_messages)
    genre = params.get("genre", "")
    hero = params.get("main_hero", "")
    
    messages = [
        {"role": "system", "content": praise_prompt},
        {
            "role": "user",
            "content": (
                f"Жанр: {genre}\nГлавный герой: {hero}\n\n"
                f"Вклад ребенка:\n{user_text}"
            )
        }
    ]
    
    praise = await send_message(messages, temperature=0.75)
    
    logger.info(f"Generated praise: length={len(praise)} chars")
    return praise.strip()
