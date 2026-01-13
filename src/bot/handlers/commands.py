"""Обработчики команд бота"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from storage.memory import clear_session

logger = logging.getLogger(__name__)
commands_router = Router()


@commands_router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    logger.info(f"Command: /start, chat_id={chat_id}, user={username}")
    await message.answer("Задайте свой вопрос")


@commands_router.message(Command("clear"))
async def clear_handler(message: Message) -> None:
    """Обработчик команды /clear - очистка истории"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    logger.info(f"Command: /clear, chat_id={chat_id}, user={username}")
    
    clear_session(chat_id)
    await message.answer("История диалога очищена. Начнем сначала!")


@commands_router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Обработчик команды /help"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    logger.info(f"Command: /help, chat_id={chat_id}, user={username}")
    
    help_text = (
        "🤖 Я - ИИ-ассистент, готовый помочь вам!\n\n"
        "Доступные команды:\n"
        "/start - Начать диалог\n"
        "/help - Показать эту справку\n"
        "/clear - Очистить историю диалога\n\n"
        "Просто напишите мне свой вопрос, и я с удовольствием отвечу!"
    )
    await message.answer(help_text)
