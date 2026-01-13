import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from llm.client import send_message
from storage.memory import add_message, get_messages, clear_session
from config import config

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    logger.info(f"Command: /start, chat_id={chat_id}, user={username}")
    await message.answer("Задайте свой вопрос")

@router.message(Command("clear"))
async def clear_handler(message: Message) -> None:
    """Обработчик команды /clear - очистка истории"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    logger.info(f"Command: /clear, chat_id={chat_id}, user={username}")
    
    clear_session(chat_id)
    await message.answer("История диалога очищена. Начнем сначала!")

@router.message(Command("help"))
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

def _validate_message_length(text: str, max_length: int) -> bool:
    """Проверка длины сообщения"""
    return len(text) <= max_length

async def _send_too_long_error(message: Message, text_length: int) -> None:
    """Отправка сообщения об ошибке длины"""
    max_length = config["max_message_length"]
    await message.answer(
        f"Сообщение слишком длинное ({text_length} символов). "
        f"Максимальная длина: {max_length} символов. "
        f"Пожалуйста, сократите ваше сообщение."
    )

async def _send_error_message(message: Message) -> None:
    """Отправка сообщения об общей ошибке"""
    await message.answer(
        "Извините, произошла временная ошибка при обработке вашего сообщения. 😔\n\n"
        "Пожалуйста, попробуйте:\n"
        "• Переформулировать вопрос\n"
        "• Или попробовать снова через минуту\n"
        "• Используйте /clear для начала нового диалога"
    )

async def _process_user_message(chat_id: int, user_text: str) -> str:
    """Обработка сообщения пользователя через LLM"""
    add_message(chat_id, "user", user_text)
    messages = get_messages(chat_id)
    llm_response = await send_message(messages)
    add_message(chat_id, "assistant", llm_response)
    return llm_response

def _log_message_received(chat_id: int, text_length: int, username: str) -> None:
    """Логирование полученного сообщения"""
    logger.info(
        f"Message received: chat_id={chat_id}, "
        f"length={text_length}, user={username}"
    )

def _log_response_sent(chat_id: int, response_length: int) -> None:
    """Логирование отправленного ответа"""
    logger.info(
        f"Response sent: chat_id={chat_id}, "
        f"response_length={response_length}"
    )

def _log_message_error(chat_id: int, error: Exception) -> None:
    """Логирование ошибки обработки сообщения"""
    error_type = type(error).__name__
    logger.error(
        f"Error handling message: chat_id={chat_id}, "
        f"error={error_type}: {error}",
        exc_info=True
    )

@router.message()
async def message_handler(message: Message) -> None:
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    user_text = message.text
    username = message.from_user.username or "unknown"
    
    if not _validate_message_length(user_text, config["max_message_length"]):
        logger.warning(
            f"Message too long: chat_id={chat_id}, "
            f"length={len(user_text)}, user={username}"
        )
        await _send_too_long_error(message, len(user_text))
        return
    
    _log_message_received(chat_id, len(user_text), username)
    
    try:
        llm_response = await _process_user_message(chat_id, user_text)
        _log_response_sent(chat_id, len(llm_response))
        await message.answer(llm_response)
    except Exception as e:
        _log_message_error(chat_id, e)
        await _send_error_message(message)