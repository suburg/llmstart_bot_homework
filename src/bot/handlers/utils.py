"""Вспомогательные функции для обработчиков бота"""
import logging
from aiogram.types import Message

from config import config

logger = logging.getLogger(__name__)


def validate_message_length(text: str, max_length: int) -> bool:
    """Проверка длины сообщения"""
    return len(text) <= max_length


async def send_too_long_error(message: Message, text_length: int) -> None:
    """Отправка сообщения об ошибке длины"""
    max_length = config["max_message_length"]
    await message.answer(
        f"Сообщение слишком длинное ({text_length} символов). "
        f"Максимальная длина: {max_length} символов. "
        f"Пожалуйста, сократите ваше сообщение."
    )


async def send_error_message(message: Message) -> None:
    """Отправка сообщения об общей ошибке"""
    await message.answer(
        "Извините, произошла временная ошибка при обработке вашего сообщения. 😔\n\n"
        "Пожалуйста, попробуйте:\n"
        "• Переформулировать вопрос\n"
        "• Или попробовать снова через минуту\n"
        "• Используйте /clear для начала нового диалога"
    )


def log_message_received(chat_id: int, text_length: int, username: str) -> None:
    """Логирование полученного сообщения"""
    logger.info(
        f"Message received: chat_id={chat_id}, "
        f"length={text_length}, user={username}"
    )


def log_response_sent(chat_id: int, response_length: int) -> None:
    """Логирование отправленного ответа"""
    logger.info(
        f"Response sent: chat_id={chat_id}, "
        f"response_length={response_length}"
    )


def log_message_error(chat_id: int, error: Exception) -> None:
    """Логирование ошибки обработки сообщения"""
    error_type = type(error).__name__
    logger.error(
        f"Error handling message: chat_id={chat_id}, "
        f"error={error_type}: {error}",
        exc_info=True
    )
