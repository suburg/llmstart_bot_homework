"""Генерация обложек историй через polza.ai Image Generation API"""
import logging
import asyncio
import httpx
from pathlib import Path

from src.config import config

logger = logging.getLogger(__name__)


async def generate_cover(
    story_id: int,
    title: str,
    genre: str,
    main_hero: str,
    author_name: str,
    story_preview: str,
    references: list[str]
) -> str:
    """
    Генерация обложки для истории через polza.ai
    
    Args:
        story_id: ID истории
        title: Название истории
        genre: Жанр истории
        main_hero: Главный герой
        author_name: Имя автора
        story_preview: Краткое содержание (первые 200 символов)
        references: Референсные произведения жанра
    
    Returns:
        Относительный путь к сохраненной обложке
    
    Raises:
        Exception: При ошибках API или сохранения файла
    """
    try:
        prompt = _create_cover_prompt(
            title, genre, main_hero, author_name, story_preview, references
        )
        logger.info(
            f"Image Generation Request: story_id={story_id}, "
            f"prompt_length={len(prompt)}, genre={genre}"
        )
        
        request_id = await _start_generation(prompt)
        logger.info(f"Image generation started: request_id={request_id}")
        
        image_url = await _wait_for_completion(request_id)
        logger.info(f"Image generation completed: url={image_url}")
        
        cover_path = await _download_and_save(image_url, story_id)
        
        logger.info(f"Image Generation Response: saved to {cover_path}")
        return cover_path
        
    except Exception as e:
        logger.error(
            f"Image Generation Error for story {story_id}: "
            f"{type(e).__name__}: {e}\n"
            f"API endpoint: {config['image_gen_base_url']}\n"
            f"Model: {config['image_gen_model']}"
        )
        raise


def _create_cover_prompt(
    title: str,
    genre: str,
    main_hero: str,
    author_name: str,
    story_preview: str,
    references: list[str]
) -> str:
    """Создать промпт для генерации обложки"""
    from src.ai.prompts import load_prompt
    
    base_prompt = load_prompt("cover_generation.txt")
    
    refs_text = ", ".join(references) if references else "классические детские книги"
    
    prompt = (
        f"{base_prompt}\n\n"
        f"Жанр: {genre}\n"
        f"Название: {title}\n"
        f"Автор: {author_name}\n"
        f"Главный герой: {main_hero}\n"
        f"Стиль референсов: {refs_text}\n\n"
        f"Краткое содержание:\n{story_preview}"
    )
    
    return prompt


async def _start_generation(prompt: str) -> str:
    """Отправить запрос на генерацию, получить request_id"""
    url = f"{config['image_gen_base_url']}/images/generations"
    headers = {
        "Authorization": f"Bearer {config['image_gen_api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["image_gen_model"],
        "prompt": prompt,
        "size": "4:3",
        "imageResolution": "2K",
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
    
    request_id = result.get("requestId")
    if not request_id:
        raise ValueError(f"No requestId in response: {result}")
    
    return request_id


async def _wait_for_completion(request_id: str, max_attempts: int = 60) -> str:
    """
    Ждать завершения генерации, получить URL изображения
    
    Args:
        request_id: ID запроса из первого запроса
        max_attempts: Максимальное количество попыток (60 * 3 сек = 180 сек = 3 минуты)
    
    Returns:
        URL сгенерированного изображения
    """
    url = f"{config['image_gen_base_url']}/images/{request_id}"
    headers = {
        "Authorization": f"Bearer {config['image_gen_api_key']}",
    }
    
    for attempt in range(max_attempts):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
        
        status = result.get("status")
        
        if status == "COMPLETED":
            image_url = result.get("url")
            if not image_url:
                raise ValueError(f"No URL in completed response: {result}")
            return image_url
        
        elif status == "FAILED":
            raise Exception(f"Image generation failed: {result}")
        
        logger.info(f"Image generation in progress: attempt {attempt + 1}/{max_attempts}")
        await asyncio.sleep(3)
    
    raise TimeoutError(f"Image generation timeout after {max_attempts} attempts")


async def _download_and_save(image_url: str, story_id: int) -> str:
    """Скачать изображение и сохранить локально"""
    covers_dir = Path(config["images_base_path"]) / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)
    
    cover_filename = f"{story_id}.png"
    cover_path = covers_dir / cover_filename
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        
        with open(cover_path, "wb") as f:
            f.write(response.content)
    
    return str(cover_path)
