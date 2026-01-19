"""Обработчики команд бота"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from storage.memory import mark_user_greeted, get_story_session, update_story_session
from story import manager
from bot.keyboards import (
    get_genre_keyboard,
    get_duration_keyboard,
    get_creativity_keyboard,
    get_who_starts_keyboard,
)

logger = logging.getLogger(__name__)
commands_router = Router()


@commands_router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    mark_user_greeted(chat_id)
    
    welcome_text = (
        "Привет! 👋 Я помогу тебе сочинить увлекательную историю!\n\n"
        "Мы будем писать её вместе, по очереди. Ты сможешь выбрать:\n"
        "📚 Жанр (сказка, приключение, фэнтези, детектив)\n"
        "⏱ Длительность (короткая, средняя, длинная)\n"
        "🦸 Имя главного героя\n"
        "✍️ Кто начнёт историю - ты или я\n\n"
        "Готов создать свою историю? Напиши /new_story"
    )
    await message.answer(welcome_text)
    logger.info(f"Command: /start, chat_id={chat_id}, user={username}")


@commands_router.message(Command("new_story"))
async def new_story_handler(message: Message) -> None:
    """Обработчик команды /new_story"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    
    response = manager.start_story_creation(chat_id)
    keyboard = get_genre_keyboard()
    await message.answer(response, reply_markup=keyboard)
    logger.info(f"Command: /new_story, chat_id={chat_id}, user={username}")


@commands_router.callback_query(F.data.startswith("genre:"))
async def process_genre_callback(callback: CallbackQuery) -> None:
    """Обработчик выбора жанра"""
    chat_id = callback.message.chat.id
    genre = callback.data.split(":")[1]
    
    response = manager.process_genre_choice(chat_id, genre)
    keyboard = get_duration_keyboard()
    
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"User {chat_id} chose genre: {genre}")


@commands_router.callback_query(F.data.startswith("duration:"))
async def process_duration_callback(callback: CallbackQuery) -> None:
    """Обработчик выбора длительности"""
    chat_id = callback.message.chat.id
    duration = callback.data.split(":")[1]
    
    response = manager.process_duration_choice(chat_id, duration)
    
    # Убираем кнопки, переходим к текстовому вводу имени героя
    await callback.message.edit_text(response)
    await callback.answer()
    logger.info(f"User {chat_id} chose duration: {duration}")


@commands_router.callback_query(F.data.startswith("creativity:"))
async def process_creativity_callback(callback: CallbackQuery) -> None:
    """Обработчик выбора уровня креативности"""
    chat_id = callback.message.chat.id
    creativity = callback.data.split(":")[1]
    
    response = manager.process_creativity_choice(chat_id, creativity)
    keyboard = get_who_starts_keyboard()
    
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"User {chat_id} chose creativity: {creativity}")


@commands_router.callback_query(F.data.startswith("starts:"))
async def process_who_starts_callback(callback: CallbackQuery) -> None:
    """Обработчик выбора кто начинает"""
    chat_id = callback.message.chat.id
    who = callback.data.split(":")[1]
    
    response, need_bot_start = manager.process_who_starts(chat_id, who)
    
    # Убираем кнопки
    await callback.message.edit_text(response)
    await callback.answer()
    logger.info(f"User {chat_id} chose who starts: {who}")
    
    # Если бот начинает - генерируем начало
    if need_bot_start:
        from ai import llm, prompts
        
        session = get_story_session(chat_id)
        params = session["params"]
        
        # Формируем промпт для начала истории
        genre_context = manager.get_genre_context(params["genre"])
        hero = params["main_hero"]
        additional = params.get("additional_heroes")
        
        story_prompt = (
            f"Начни {genre_context} про главного героя по имени {hero}. "
        )
        if additional:
            story_prompt += f"Другие персонажи: {additional}. "
        story_prompt += "Напиши только 2-3 первых предложения, которые заинтересуют ребенка."
        
        # Получаем температуру из параметров
        creativity = params.get("creativity_level", "medium")
        temperature = manager.get_temperature_for_creativity(creativity)
        
        system_prompt = prompts.load_system_prompt()
        bot_start = await llm.send_message(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": story_prompt}
            ],
            temperature=temperature
        )
        
        # Сохраняем начало в историю
        session["content"].append({"role": "assistant", "content": bot_start})
        update_story_session(chat_id, {"content": session["content"]})
        
        await callback.message.answer(bot_start)
        await callback.message.answer("\nТеперь твоя очередь! Продолжи историю (2-3 предложения).")
        logger.info(f"Bot started story for user {chat_id}")


@commands_router.callback_query(F.data.startswith("complete:"))
async def handle_completion_choice(callback: CallbackQuery) -> None:
    """Обработка выбора завершения истории"""
    from storage.memory import clear_story_session
    from ai import llm, prompts
    
    chat_id = callback.message.chat.id
    choice = callback.data.split(":")[1]
    
    session = get_story_session(chat_id)
    
    if not session:
        await callback.answer("Сессия истекла")
        return
    
    if choice == "yes":
        # Переходим в режим написания финала
        update_story_session(chat_id, {"state": "writing_finale"})
        
        hero_name = session["params"].get("main_hero", "герой")
        await callback.message.edit_text(
            "История подходит к концу! 📖✨\n\nХочешь завершить историю или продолжить ещё немного?"
        )
        await callback.message.answer(
            f"Отлично! 📝✨\n\n"
            f"Теперь напиши финал истории — как всё закончилось для {hero_name}?"
        )
        
        logger.info(f"User {chat_id} will write finale")
        
    else:
        # Продолжаем историю - увеличиваем лимит на 3 пары
        manager.extend_story_limit(chat_id)
        
        # Генерируем ответ бота на последнее сообщение
        if session["content"] and session["content"][-1]["role"] == "user":
            params = session["params"]
            genre_context = manager.get_genre_context(params["genre"])
            
            # Получаем температуру из параметров
            creativity = params.get("creativity_level", "medium")
            temperature = manager.get_temperature_for_creativity(creativity)
            
            system_prompt = prompts.load_system_prompt()
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({
                "role": "system",
                "content": f"Жанр: {genre_context}. Герой: {params['main_hero']}."
            })
            messages.extend(session["content"])
            
            bot_response = await llm.send_message(messages, temperature=temperature)
            session["content"].append({"role": "assistant", "content": bot_response})
            
            update_story_session(chat_id, {"state": "storytelling", "content": session["content"]})
            
            await callback.message.edit_text(
                "История подходит к концу! 📖✨\n\nХочешь завершить историю или продолжить ещё немного?"
            )
            await callback.message.answer(bot_response)
            await callback.message.answer("Продолжай историю дальше! ✍️")
            
            logger.info(f"User {chat_id} chose to continue story")
        else:
            update_story_session(chat_id, {"state": "storytelling"})
            await callback.message.edit_text(
                "История подходит к концу! 📖✨\n\nХочешь завершить историю или продолжить ещё немного?"
            )
            await callback.message.answer("Хорошо! Продолжай историю! ✍️")
    
    await callback.answer()


@commands_router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Обработчик команды /help"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    
    help_text = (
        "🤖 Помощь по боту\n\n"
        "Я помогаю детям сочинять истории! Мы пишем по очереди, "
        "развивая сюжет вместе.\n\n"
        "Доступные команды:\n"
        "/start - Приветствие и описание\n"
        "/new_story - Создать новую историю\n"
        "/help - Эта справка\n\n"
        "Как это работает:\n"
        "1. Создай историю с помощью /new_story\n"
        "2. Выбери жанр, длительность и имя героя\n"
        "3. Мы по очереди пишем по 2-3 предложения\n"
        "4. Когда история будет готова, я помогу её завершить\n\n"
        "Удачи в творчестве! ✨"
    )
    await message.answer(help_text)
    logger.info(f"Command: /help, chat_id={chat_id}, user={username}")
