import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    logger.info(f"Start command from chat_id: {message.chat.id}")
    await message.answer("Hello World")