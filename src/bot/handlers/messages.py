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
        # Добавляем сообщение пользователя
        session["content"].append({"role": "user", "content": text})
        update_story_session(chat_id, {"content": session["content"]})
        
        # Проверяем нужно ли предложить завершение ПЕРЕД генерацией ответа бота
        pairs_count = manager.count_message_pairs(session["content"])
        current_limit = session.get("current_limit", 10)
        
        if manager.should_offer_completion(pairs_count, current_limit):
            from bot.keyboards import get_completion_keyboard
            
            update_story_session(chat_id, {"state": "awaiting_completion_choice"})
            
            await message.answer(
                "История подходит к концу! 📖✨\n\nХочешь завершить историю или продолжить ещё немного?",
                reply_markup=get_completion_keyboard()
            )
            logger.info(f"Offered completion to user {chat_id} at {pairs_count} pairs")
            return
        
        # Генерируем продолжение от бота
        params = session["params"]
        genre_context = manager.get_genre_context(params["genre"])
        
        system_prompt = prompts.load_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        # Базовый контекст жанра и героя
        genre_instruction = f"Жанр истории: {genre_context}. Главный герой: {params['main_hero']}."
        
        # Добавляем инструкцию для подведения к концу если близко
        ending_instruction = manager.get_ending_instruction(pairs_count, current_limit)
        if ending_instruction:
            genre_instruction += f" {ending_instruction}"
        
        messages.append({"role": "system", "content": genre_instruction})
        messages.extend(session["content"])
        
        bot_response = await client.send_message(messages)
        
        # Сохраняем ответ бота
        session["content"].append({"role": "assistant", "content": bot_response})
        update_story_session(chat_id, {"content": session["content"]})
        
        await message.answer(bot_response)
        logger.info(f"Story continues for user {chat_id}, pairs: {len(session['content'])//2}")
    
    elif state == "writing_finale":
        # Ребенок написал финал истории
        session["content"].append({"role": "user", "content": text})
        
        # Генерируем короткий завершающий ответ от бота
        params = session["params"]
        genre_context = manager.get_genre_context(params["genre"])
        
        system_prompt = prompts.load_system_prompt()
        finale_instruction = (
            "Это финальное сообщение истории. "
            "Напиши короткое завершение (1-2 предложения), которое красиво закроет историю."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Жанр: {genre_context}. Герой: {params['main_hero']}. {finale_instruction}"}
        ]
        messages.extend(session["content"])
        
        bot_finale = await client.send_message(messages)
        session["content"].append({"role": "assistant", "content": bot_finale})
        update_story_session(chat_id, {"content": session["content"]})
        
        await message.answer(bot_finale)
        await message.answer("Готовлю финальную версию истории... ✨")
        
        # Финализация
        from story import formatter
        result = await formatter.finalize_story(
            session["content"],
            session["params"]
        )
        
        # Отправляем результат
        final_message = (
            f"🎉 **{result['title']}**\n\n"
            f"{result['final_text']}\n\n"
            f"✨ История завершена! Отличная работа!"
        )
        
        await message.answer(final_message, parse_mode="Markdown")
        
        # Очищаем сессию
        from storage.memory import clear_story_session
        clear_story_session(chat_id)
        
        logger.info(f"Story completed for user {chat_id}: {result['title']}")
    
    else:
        # Неожиданное состояние
        await message.answer("Что-то пошло не так. Попробуй начать заново: /new_story")
        logger.warning(f"Unexpected state for user {chat_id}: {state}")
