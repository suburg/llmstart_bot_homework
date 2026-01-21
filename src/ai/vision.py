"""Анализ изображений через Vision API"""
import logging
import base64
from pathlib import Path

from src.config import config

logger = logging.getLogger(__name__)


async def analyze_image(image_path: str) -> str:
    """
    Анализ изображения для определения стиля и темы
    
    Args:
        image_path: Путь к изображению
    
    Returns:
        Описание стиля и темы изображения для использования в промпте
    
    Raises:
        Exception: При ошибках API
    """
    try:
        import httpx
        
        # Читаем изображение и кодируем в base64
        image_data = _encode_image(image_path)
        
        logger.info(
            f"Vision API Request: image_path={image_path}, "
            f"model={config['vision_model']}"
        )
        
        # Формируем запрос к Vision API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Опиши это изображение для создания детской истории. "
                            "Укажи: стиль (реалистичный, мультяшный, акварельный и т.д.), "
                            "настроение (веселое, таинственное, волшебное), "
                            "основные элементы (персонажи, место, время суток), "
                            "и возможный сюжет или события, которые могли происходить на изображении. "
                            "Ответ дай в 3-5 предложениях."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        # Запрос к Vision API
        url = f"{config['vision_base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config['vision_api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config["vision_model"],
            "messages": messages,
            "max_tokens": 300,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        description = result["choices"][0]["message"]["content"]
        
        logger.info(
            f"Vision API Response: length={len(description)}, "
            f"description='{description[:100]}...'"
        )
        
        return description
        
    except Exception as e:
        logger.error(
            f"Vision API Error for image {image_path}: "
            f"{type(e).__name__}: {e}"
        )
        raise


def _encode_image(image_path: str) -> str:
    """Кодировать изображение в base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
