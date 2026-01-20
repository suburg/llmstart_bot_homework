"""Обработчик текстовых и голосовых сообщений"""
import logging
import os
from tempfile import NamedTemporaryFile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message

from src.storage.memory import (
    get_story_session,
    update_story_session,
    is_user_greeted,
    mark_user_greeted,
)
from src.story import manager
from src.bot.keyboards import get_who_starts_keyboard, get_creativity_keyboard
from src.ai import llm, prompts, speech

logger = logging.getLogger(__name__)
messages_router = Router()


async def process_text_input(chat_id: int, text: str, message: Message) -> None:
    """
    Обработка текстового ввода (из текста или голоса)
    
    Args:
        chat_id: ID чата пользователя
        text: Текст для обработки
        message: Message объект для отправки ответов
    """
    if text is None:
        logger.error(f"process_text_input called with None text for chat_id={chat_id}")
        await message.answer("Произошла ошибка. Попробуй написать текстом.")
        return
    
    logger.info(f"process_text_input called: chat_id={chat_id}, text_len={len(text)}, text='{text[:50]}...'")
    
    session = get_story_session(chat_id)
    
    # Если нет активной сессии
    if not session:
        await message.answer("Давай создадим историю! Напиши /new_story")
        return
    
    state = session.get("state")
    logger.info(f"Session state for {chat_id}: {state}")
    
    # Обработка ввода имени героя
    if state == "entering_hero_name":
        response = manager.process_hero_name(chat_id, text)
        await message.answer(response)
        logger.info(f"User {chat_id} entered hero name: {text}")
    
    # Обработка ввода дополнительных персонажей
    elif state == "entering_additional_heroes":
        response = manager.process_additional_heroes(chat_id, text)
        keyboard = get_creativity_keyboard()
        await message.answer(response, reply_markup=keyboard)
        logger.info(f"User {chat_id} entered additional heroes: {text}")
        
    elif state == "storytelling":
        # Добавляем сообщение пользователя
        logger.info(f"Adding user message to story: chat_id={chat_id}, content_len={len(text)}")
        session["content"].append({"role": "user", "content": text})
        update_story_session(chat_id, {"content": session["content"]})
        
        # Сохраняем в БД
        from src.storage import database
        if session.get("story_id"):
            database.update_story_content(session["story_id"], session["content"])
        
        # Проверяем нужно ли предложить завершение ПЕРЕД генерацией ответа бота
        pairs_count = manager.count_message_pairs(session["content"])
        current_limit = session.get("current_limit", 10)
        
        if manager.should_offer_completion(pairs_count, current_limit):
            from src.bot.keyboards import get_completion_keyboard
            
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
        
        # Получаем температуру из параметров
        creativity = params.get("creativity_level", "medium")
        temperature = manager.get_temperature_for_creativity(creativity)
        
        system_prompt = prompts.load_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        # Базовый контекст жанра и героя
        genre_instruction = f"Жанр истории: {genre_context}. Главный герой: {params['main_hero']}."
        additional = params.get("additional_heroes")
        if additional:
            genre_instruction += f" Другие персонажи: {additional}."
        
        # Добавляем инструкцию для подведения к концу если близко
        ending_instruction = manager.get_ending_instruction(pairs_count, current_limit)
        if ending_instruction:
            genre_instruction += f" {ending_instruction}"
        
        messages.append({"role": "system", "content": genre_instruction})
        
        # Фильтруем сообщения с пустыми значениями
        valid_content = [
            msg for msg in session["content"]
            if isinstance(msg, dict) and 
               msg.get("role") and 
               msg.get("content") and
               isinstance(msg.get("content"), str)
        ]
        
        if len(valid_content) < len(session["content"]):
            invalid_msgs = [
                msg for msg in session["content"]
                if msg not in valid_content
            ]
            logger.warning(
                f"Filtered out {len(session['content']) - len(valid_content)} "
                f"invalid messages for user {chat_id}: {invalid_msgs}"
            )
        
        messages.extend(valid_content)
        
        bot_response = await llm.send_message(messages, temperature=temperature)
        
        # Сохраняем ответ бота
        session["content"].append({"role": "assistant", "content": bot_response})
        update_story_session(chat_id, {"content": session["content"]})
        
        # Сохраняем в БД
        if session.get("story_id"):
            database.update_story_content(session["story_id"], session["content"])
        
        await message.answer(bot_response)
        logger.info(f"Story continues for user {chat_id}, pairs: {len(session['content'])//2}")
    
    elif state == "writing_finale":
        # Ребенок написал финал истории
        session["content"].append({"role": "user", "content": text})
        
        # Сохраняем в БД
        from src.storage import database
        if session.get("story_id"):
            database.update_story_content(session["story_id"], session["content"])
        
        # Генерируем короткий завершающий ответ от бота
        params = session["params"]
        genre_context = manager.get_genre_context(params["genre"])
        
        # Получаем температуру из параметров
        creativity = params.get("creativity_level", "medium")
        temperature = manager.get_temperature_for_creativity(creativity)
        
        system_prompt = prompts.load_system_prompt()
        finale_instruction = (
            "Это финальное сообщение истории. "
            "Напиши короткое завершение (1-2 предложения), которое красиво закроет историю."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Жанр: {genre_context}. Герой: {params['main_hero']}. {finale_instruction}"}
        ]
        
        # Фильтруем сообщения с пустыми значениями
        valid_content = [
            msg for msg in session["content"]
            if msg.get("role") and msg.get("content")
        ]
        messages.extend(valid_content)
        
        bot_finale = await llm.send_message(messages, temperature=temperature)
        session["content"].append({"role": "assistant", "content": bot_finale})
        update_story_session(chat_id, {"content": session["content"]})
        
        # Сохраняем в БД
        if session.get("story_id"):
            database.update_story_content(session["story_id"], session["content"])
        
        await message.answer(bot_finale)
        await message.answer("Готовлю финальную версию истории... ✨")
        
        # Финализация
        from src.story import formatter
        result = await formatter.finalize_story(
            session["content"],
            session["params"],
            session.get("story_id")  # Передаем story_id для сохранения в БД
        )
        
        # Отправляем название
        await message.answer(f"📖 <b>{result['title']}</b>", parse_mode="HTML")
        
        # Отправляем обложку если есть
        if result.get("cover_url"):
            from pathlib import Path
            from aiogram.types import FSInputFile
            
            cover_path = Path(result["cover_url"])
            if cover_path.exists():
                photo = FSInputFile(cover_path)
                await message.answer_photo(photo)
            else:
                logger.warning(f"Cover file not found: {result['cover_url']}")
        
        # Отправляем финальный текст
        await message.answer(result["final_text"])
        
        # Отправляем похвалу отдельным сообщением
        if result.get("praise"):
            praise_message = f"✨ <b>Отличная работа!</b> ✨\n\n{result['praise']}"
            await message.answer(praise_message, parse_mode="HTML")
        
        # Очищаем сессию
        from src.storage.memory import clear_story_session
        clear_story_session(chat_id)
        
        logger.info(f"Story completed for user {chat_id}: {result['title']}")
    
    else:
        # Неожиданное состояние
        await message.answer("Что-то пошло не так. Попробуй начать заново: /new_story")
        logger.warning(f"Unexpected state for user {chat_id}: {state}")


@messages_router.message(F.text)
async def message_handler(message: Message) -> None:
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    text = message.text
    
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
    
    await process_text_input(chat_id, text, message)


@messages_router.message(F.voice)
async def voice_handler(message: Message) -> None:
    """Обработчик голосовых сообщений"""
    chat_id = message.chat.id
    
    # Проверка приветствия
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
    
    # Проверка, что пользователь в процессе сочинения
    if not session or session.get("state") not in ["storytelling", "writing_finale"]:
        await message.answer(
            "Голосовые сообщения можно использовать только во время сочинения истории.\n"
            "Давай создадим историю! Напиши /new_story"
        )
        return
    
    # Скачиваем голосовое сообщение
    temp_path = None
    try:
        file = await message.bot.get_file(message.voice.file_id)
        
        # Создаем временный файл для хранения аудио
        with NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            temp_path = temp_file.name
            await message.bot.download_file(file.file_path, temp_path)
        
        logger.info(f"Voice message downloaded for user {chat_id}")
        
        # Распознаем голос
        await message.answer("Распознаю голос... 🎤")
        text = await speech.transcribe_voice(temp_path)
        
        # Удаляем временный файл
        os.unlink(temp_path)
        temp_path = None
        
        if not text:
            await message.answer(
                "Не удалось распознать голос. Попробуй ещё раз или напиши текстом."
            )
            logger.warning(f"Empty transcription for user {chat_id}")
            return
        
        logger.info(f"Voice transcribed for user {chat_id}: {len(text)} chars, text='{text}'")
        
        # Показываем распознанный текст
        await message.answer(f"Ты сказал: \"{text}\"")
        
        # Обрабатываем распознанный текст
        logger.info(f"Processing voice input as text for user {chat_id}")
        await process_text_input(chat_id, text, message)
        
    except Exception as e:
        logger.error(f"Voice processing error for user {chat_id}: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при обработке голосового сообщения. "
            "Попробуй написать текстом или отправь голос ещё раз."
        )
        
        # Удаляем временный файл если он существует
        if temp_path and Path(temp_path).exists():
            os.unlink(temp_path)
