"""Обработчики команд бота"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from storage.memory import (
    clear_session,
    reset_system_prompt,
    get_system_prompt,
    set_custom_prompt,
)

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
    reset_system_prompt(chat_id)
    await message.answer(
        "История диалога очищена. Системный промпт сброшен. Начнем сначала!"
    )


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
        "/clear - Очистить историю и сбросить промпт\n"
        "/prompt - Показать текущий системный промпт\n"
        "/setprompt <текст> - Установить новый системный промпт\n\n"
        "Просто напишите мне свой вопрос, и я с удовольствием отвечу!"
    )
    await message.answer(help_text)


@commands_router.message(Command("prompt"))
async def prompt_handler(message: Message) -> None:
    """Обработчик команды /prompt - показать текущий промпт"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    logger.info(f"Command: /prompt, chat_id={chat_id}, user={username}")
    
    current_prompt = get_system_prompt(chat_id)
    
    response = f"📝 Текущий системный промпт:\n\n{current_prompt}"
    await message.answer(response)


@commands_router.message(Command("setprompt"))
async def setprompt_handler(message: Message) -> None:
    """Обработчик команды /setprompt - установить новый промпт"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    logger.info(f"Command: /setprompt, chat_id={chat_id}, user={username}")
    
    command_text = message.text or ""
    parts = command_text.split(maxsplit=1)
    
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "❌ Использование: /setprompt <новый промпт>\n\n"
            "Пример: /setprompt Ты - дружелюбный помощник"
        )
        return
    
    new_prompt = parts[1].strip()
    set_custom_prompt(chat_id, new_prompt)
    
    await message.answer(
        "✅ Системный промпт обновлен!\n"
        "История диалога очищена.\n\n"
        "Используйте /prompt для просмотра текущего промпта."
    )
