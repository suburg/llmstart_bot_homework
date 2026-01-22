import logging
import asyncio
import httpx
from openai import AsyncOpenAI
import openai

from src.config import config

logger = logging.getLogger(__name__)

def create_llm_client() -> AsyncOpenAI:
    """Создание клиента для OpenRouter"""
    timeout = config.get("llm_timeout", 30.0)
    return AsyncOpenAI(
        base_url=config["llm_base_url"],
        api_key=config["llm_api_key"],
        timeout=httpx.Timeout(timeout, connect=5.0),
        max_retries=0,  # отключаем встроенный retry OpenAI SDK
    )


def is_retryable_error(e: Exception) -> bool:
    """
    Проверяет, можно ли повторить запрос при данной ошибке
    
    Args:
        e: Исключение для проверки
        
    Returns:
        True если ошибка временная и стоит повторить запрос
    """
    # 1. Timeout/Network errors
    if isinstance(e, (asyncio.TimeoutError, httpx.TimeoutException, httpx.ConnectError)):
        return True
    
    # 2. Rate limits
    if isinstance(e, openai.RateLimitError):
        return True
    
    # 3. Server errors (5xx)
    if hasattr(e, 'status_code'):
        try:
            if int(e.status_code) >= 500:
                return True
        except (ValueError, TypeError):
            pass
    
    # 4. polza.ai специфика: 400 с временной недоступностью
    if isinstance(e, openai.BadRequestError):
        error_msg = str(e).lower()
        # Проверяем текст ошибки, а не только код
        if 'temporarily unavailable' in error_msg or 'llm_request_error' in error_msg:
            return True
    
    return False


async def send_message(
    messages: list[dict[str, str]], 
    model: str | None = None,
    temperature: float = 0.7
) -> str:
    """
    Отправка сообщения в LLM с retry механизмом
    
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
    
    # Параметры retry из конфигурации
    max_retries = config.get("llm_max_retries", 3)
    base_delay = config.get("llm_retry_delay", 2.0)
    
    logger.info(
        f"LLM Request: model={model}, temp={temperature}, "
        f"messages_count={len(messages)}"
    )
    
    # Проверяем наличие null значений
    for i, msg in enumerate(messages):
        if not msg.get("role"):
            logger.error(f"Message {i} has null role: {msg}")
        if not msg.get("content"):
            logger.error(f"Message {i} has null content: {msg}")
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            
            answer = response.choices[0].message.content
            logger.info(f"LLM Response: length={len(answer)} chars")
            
            return answer
            
        except Exception as e:
            last_error = e
            logger.error(f"LLM Error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
            
            # Проверяем, можно ли повторить запрос
            if attempt < max_retries - 1 and is_retryable_error(e):
                # Экспоненциальная задержка: 2s, 5s, 10s
                delay = base_delay * (2.5 ** attempt)
                logger.info(f"Retrying after {delay:.1f} seconds...")
                await asyncio.sleep(delay)
            else:
                # Последняя попытка или постоянная ошибка
                break
    
    # Все попытки исчерпаны
    logger.error(f"LLM Request failed after {max_retries} attempts")
    raise last_error


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
