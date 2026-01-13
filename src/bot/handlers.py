import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from llm.client import send_message
from storage.memory import add_message, get_messages, clear_session

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    logger.info(f"Start command from chat_id: {message.chat.id}")
    await message.answer("Задайте свой вопрос")

@router.message(Command("clear"))
async def clear_handler(message: Message) -> None:
    """Обработчик команды /clear - очистка истории"""
    chat_id = message.chat.id
    logger.info(f"Clear command from chat_id: {chat_id}")
    
    clear_session(chat_id)
    await message.answer("История диалога очищена. Начнем сначала!")

@router.message()
async def message_handler(message: Message) -> None:
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    user_text = message.text
    
    logger.info(f"Message from chat_id: {chat_id}, length: {len(user_text)}")
    
    try:
        # Добавляем сообщение пользователя в историю
        add_message(chat_id, "user", user_text)
        
        # Получаем всю историю для контекста
        messages = get_messages(chat_id)
        
        # Отправляем в LLM
        llm_response = await send_message(messages)
        
        # Сохраняем ответ бота в историю
        add_message(chat_id, "assistant", llm_response)
        
        await message.answer(llm_response)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await message.answer(
            "Извините, произошла ошибка при обработке вашего сообщения. "
            "Попробуйте еще раз."
        )