"""Обработчик текстовых сообщений"""
import logging
from aiogram import Router
from aiogram.types import Message

from llm.client import send_message
from storage.memory import add_message, get_messages
from config import config
from .utils import (
    validate_message_length,
    send_too_long_error,
    send_error_message,
    log_message_received,
    log_response_sent,
    log_message_error,
)

logger = logging.getLogger(__name__)
messages_router = Router()


async def process_user_message(chat_id: int, user_text: str) -> str:
    """Обработка сообщения пользователя через LLM"""
    add_message(chat_id, "user", user_text)
    messages = get_messages(chat_id)
    llm_response = await send_message(messages)
    add_message(chat_id, "assistant", llm_response)
    return llm_response


@messages_router.message()
async def message_handler(message: Message) -> None:
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    user_text = message.text
    username = message.from_user.username or "unknown"
    
    if not validate_message_length(user_text, config["max_message_length"]):
        logger.warning(
            f"Message too long: chat_id={chat_id}, "
            f"length={len(user_text)}, user={username}"
        )
        await send_too_long_error(message, len(user_text))
        return
    
    log_message_received(chat_id, len(user_text), username)
    
    try:
        llm_response = await process_user_message(chat_id, user_text)
        log_response_sent(chat_id, len(llm_response))
        await message.answer(llm_response)
    except Exception as e:
        log_message_error(chat_id, e)
        await send_error_message(message)
