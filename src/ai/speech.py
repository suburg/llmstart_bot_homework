import logging
import base64
from pathlib import Path
import httpx

from src.config import config

logger = logging.getLogger(__name__)


async def transcribe_voice(file_path: str) -> str:
    """
    Конвертация голосового сообщения в текст
    
    Args:
        file_path: Путь к аудио файлу
    
    Returns:
        Распознанный текст
    
    Raises:
        Exception: При ошибках API или файла
    """
    try:
        file_size = Path(file_path).stat().st_size / 1024  # KB
        logger.info(f"Speech-to-Text Request: file_size={file_size:.2f}KB")
        
        # Читаем файл и кодируем в base64 (для polza.ai)
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Polza.ai требует data URI формат через прямой HTTP запрос
        data_uri = f"data:audio/ogg;base64,{audio_base64}"
        
        # Прямой HTTP запрос к polza.ai (их API отличается от OpenAI)
        url = f"{config['speech_base_url']}/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {config['speech_api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config["speech_model"],
            "file": data_uri,
            "language": "ru",
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        text = result.get("text", "").strip()
        logger.info(f"Speech-to-Text Response: length={len(text)} chars")
        
        return text
        
    except Exception as e:
        logger.error(
            f"Speech-to-Text Error: {type(e).__name__}: {e}\n"
            f"API endpoint: {config['speech_base_url']}\n"
            f"Model: {config['speech_model']}\n"
            f"File: {file_path}"
        )
        raise
