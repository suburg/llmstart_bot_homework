"""Обработчик текстовых сообщений"""
import logging
from aiogram import Router
from aiogram.types import Message

from storage.memory import (
    get_story_session,
    update_story_session,
    is_user_greeted,
    mark_user_greeted,
)
from story import manager
from bot.keyboards import get_who_starts_keyboard
from llm import client, prompts

logger = logging.getLogger(__name__)
messages_router = Router()


@messages_router.message()
async def message_handler(message: Message) -> None:
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    text = message.text
    username = message.from_user.username or "unknown"
    
    # Автоматическое приветствие для новых пользователей
    if not is_user_greeted(chat_id):
        mark_user_greeted(chat_id)
        welcome_text = (
            "Привет! 👋 Я помогу тебе сочинить увлекательную историю!\n\n"
            "Напиши /new_story чтобы начать, или /help для справки."
        )
        await message.answer(welcome_text)
        logger.info(f"Auto-greeted new user {chat_id}")
        return
    
    session = get_story_session(chat_id)
    
    # Если нет активной сессии
    if not session:
        await message.answer("Давай создадим историю! Напиши /new_story")
        return
    
    state = session.get("state")
    
    # Обработка ввода имени героя (единственный текстовый ввод в выборе параметров)
    if state == "entering_hero_name":
        response = manager.process_hero_name(chat_id, text)
        keyboard = get_who_starts_keyboard()
        await message.answer(response, reply_markup=keyboard)
        logger.info(f"User {chat_id} entered hero name: {text}")
        
    elif state == "storytelling":
        # Процесс сочинения - добавляем сообщение пользователя
        session["content"].append({"role": "user", "content": text})
        update_story_session(chat_id, {"content": session["content"]})
        
        # Генерируем продолжение от бота
        params = session["params"]
        genre_context = manager.get_genre_context(params["genre"])
        
        system_prompt = prompts.load_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем контекст жанра
        messages.append({
            "role": "system",
            "content": f"Жанр истории: {genre_context}. Главный герой: {params['main_hero']}."
        })
        
        # Добавляем историю
        messages.extend(session["content"])
        
        bot_response = await client.send_message(messages)
        
        # Сохраняем ответ бота
        session["content"].append({"role": "assistant", "content": bot_response})
        update_story_session(chat_id, {"content": session["content"]})
        
        await message.answer(bot_response)
        logger.info(f"Story continues for user {chat_id}, pairs: {len(session['content'])//2}")
    
    else:
        # Неожиданное состояние
        await message.answer("Что-то пошло не так. Попробуй начать заново: /new_story")
        logger.warning(f"Unexpected state for user {chat_id}: {state}")
