import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from llm.client import send_message

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    logger.info(f"Start command from chat_id: {message.chat.id}")
    await message.answer("Задайте свой вопрос")

@router.message()
async def message_handler(message: Message) -> None:
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    user_text = message.text
    
    logger.info(f"Message from chat_id: {chat_id}, length: {len(user_text)}")
    
    try:
        messages = [
            {"role": "user", "content": user_text}
        ]
        
        llm_response = await send_message(messages)
        await message.answer(llm_response)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await message.answer(
            "Извините, произошла ошибка при обработке вашего сообщения. "
            "Попробуйте еще раз."
        )