"""Обработчики команд бота"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from src.storage.memory import mark_user_greeted, get_story_session, update_story_session
from src.story import manager
from src.bot.keyboards import (
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
        "Привет! 👋 СочиНяшка поможет тебе сочинить увлекательную историю!\n\n"
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
    
    response, had_active = manager.start_story_creation(chat_id)
    keyboard = get_genre_keyboard()
    await message.answer(response, reply_markup=keyboard)
    logger.info(f"Command: /new_story, chat_id={chat_id}, user={username}, abandoned_old={had_active}")


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
        from src.ai import llm, prompts
        from src.storage import database
        
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
        
        # Сохраняем в БД
        if session.get("story_id"):
            database.update_story_content(session["story_id"], session["content"])
        
        await callback.message.answer(bot_start)
        await callback.message.answer("\nТеперь твоя очередь! Продолжи историю (2-3 предложения).")
        logger.info(f"Bot started story for user {chat_id}")


@commands_router.callback_query(F.data.startswith("complete:"))
async def handle_completion_choice(callback: CallbackQuery) -> None:
    """Обработка выбора завершения истории"""
    from src.storage.memory import clear_story_session
    from src.ai import llm, prompts
    
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
        from src.storage import database
        
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
                    f"handle_completion_choice: Filtered {len(session['content']) - len(valid_content)} "
                    f"invalid messages for user {chat_id}: {invalid_msgs}"
                )
            
            messages.extend(valid_content)
            
            bot_response = await llm.send_message(messages, temperature=temperature)
            session["content"].append({"role": "assistant", "content": bot_response})
            
            update_story_session(chat_id, {"state": "storytelling", "content": session["content"]})
            
            # Сохраняем в БД
            if session.get("story_id"):
                database.update_story_content(session["story_id"], session["content"])
            
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


@commands_router.message(Command("my_stories"))
async def my_stories_handler(message: Message) -> None:
    """Обработчик команды /my_stories - показать список историй"""
    from src.storage import database
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    
    stories = database.get_user_stories(chat_id)
    
    if not stories:
        await message.answer("У тебя пока нет сохранённых историй. Создай новую: /new_story")
        logger.info(f"Command: /my_stories, chat_id={chat_id}, no stories")
        return
    
    # Формируем список с inline-кнопками
    text = "📚 Твои истории:\n\n"
    keyboard = InlineKeyboardBuilder()
    
    genres = manager.load_genres()
    
    for story in stories:
        status_emoji = "✅" if story["status"] == "completed" else ("⚠️" if story["status"] == "abandoned" else "✍️")
        title = story.get("title") or f"История #{story['id']}"
        genre_info = genres.get(story["genre"], {})
        genre_name = genre_info.get("name", story["genre"])
        
        text += f"{status_emoji} **{title}**\n"
        text += f"   Жанр: {genre_name}, Герой: {story['main_hero']}\n\n"
        
        # Ограничиваем длину названия для кнопки
        button_title = title[:30] + "..." if len(title) > 30 else title
        keyboard.button(
            text=f"{status_emoji} {button_title}",
            callback_data=f"view_story:{story['id']}"
        )
    
    keyboard.adjust(1)
    await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    logger.info(f"Command: /my_stories, chat_id={chat_id}, user={username}, stories={len(stories)}")


@commands_router.callback_query(F.data.startswith("view_story:"))
async def view_story_callback(callback: CallbackQuery) -> None:
    """Обработчик просмотра истории"""
    from src.storage import database
    from src.bot.keyboards import get_story_actions_keyboard
    import json
    
    story_id = int(callback.data.split(":")[1])
    story = database.get_story_by_id(story_id)
    
    if not story:
        await callback.answer("История не найдена")
        return
    
    genres = manager.load_genres()
    genre_info = genres.get(story["genre"], {})
    genre_name = genre_info.get("name", story["genre"])
    
    # Формируем сообщение
    if story["status"] == "completed":
        # Показываем финальную версию
        text = f"📖 **{story['title']}**\n\n"
        text += f"Жанр: {genre_name}\n"
        text += f"Герой: {story['main_hero']}\n\n"
        text += story["final_text"]
    else:
        # Показываем процесс сочинения
        title = story.get("title") or f"История #{story['id']}"
        text = f"📝 **{title}**\n\n"
        text += f"Статус: {'✍️ В процессе' if story['status'] == 'in_progress' else '⚠️ Не завершена'}\n"
        text += f"Жанр: {genre_name}\n"
        text += f"Герой: {story['main_hero']}\n\n"
        
        # Показываем процесс сочинения
        content = json.loads(story.get("content", "[]"))
        if content:
            text += "**Процесс сочинения:**\n\n"
            for msg in content[:10]:  # Первые 10 сообщений
                role_emoji = "👤" if msg["role"] == "user" else "🤖"
                text += f"{role_emoji} {msg['content']}\n\n"
            
            if len(content) > 10:
                text += f"... ещё {len(content) - 10} сообщений\n\n"
        
        if story["status"] == "in_progress":
            text += "✍️ Продолжай писать историю!"
    
    # Добавляем клавиатуру с действиями
    keyboard = get_story_actions_keyboard(story_id)
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    logger.info(f"User {callback.message.chat.id} viewed story {story_id}")


@commands_router.callback_query(F.data.startswith("delete_story:"))
async def delete_story_request(callback: CallbackQuery) -> None:
    """Запрос подтверждения удаления истории"""
    from src.storage import database
    from src.bot.keyboards import get_delete_confirmation_keyboard
    
    story_id = int(callback.data.split(":")[1])
    story = database.get_story_by_id(story_id)
    
    if not story:
        await callback.answer("История не найдена")
        return
    
    title = story.get("title") or f"История #{story['id']}"
    confirmation_text = (
        f"⚠️ Точно удалить историю **'{title}'**?\n\n"
        "Это действие нельзя будет отменить."
    )
    
    keyboard = get_delete_confirmation_keyboard(story_id)
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"User {callback.message.chat.id} requested delete for story {story_id}")


@commands_router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_story(callback: CallbackQuery) -> None:
    """Подтверждение удаления истории"""
    from src.storage import database
    
    chat_id = callback.message.chat.id
    story_id = int(callback.data.split(":")[1])
    story = database.get_story_by_id(story_id)
    
    if not story:
        await callback.answer("История не найдена")
        return
    
    # Проверяем что это история пользователя
    if story["user_id"] != chat_id:
        await callback.answer("Это не твоя история!")
        return
    
    title = story.get("title") or f"История #{story['id']}"
    
    # Удаляем историю
    database.delete_story(story_id)
    
    await callback.message.edit_text(
        f"✅ История **'{title}'** удалена.",
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"User {chat_id} deleted story {story_id}: {title}")


@commands_router.callback_query(F.data.startswith("cancel_delete:"))
async def cancel_delete_story(callback: CallbackQuery) -> None:
    """Отмена удаления истории"""
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.answer()
    logger.info(f"User {callback.message.chat.id} cancelled story deletion")


@commands_router.callback_query(F.data == "back_to_stories")
async def back_to_stories_callback(callback: CallbackQuery) -> None:
    """Возврат к списку историй"""
    await callback.message.delete()
    await callback.answer()
    
    # Имитируем команду /my_stories - создаем псевдо-сообщение
    from aiogram.types import User, Chat
    
    # Создаем новое сообщение для обработки
    pseudo_message = Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        from_user=callback.from_user
    )
    
    await my_stories_handler(pseudo_message)


@commands_router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Обработчик команды /help"""
    chat_id = message.chat.id
    username = message.from_user.username or "unknown"
    
    help_text = (
        "🎭 **Как сочинять истории:**\n\n"
        "/new\\_story - создать новую историю\n"
        "/my\\_stories - посмотреть все мои истории\n"
        "/help - показать эту справку\n\n"
        "**Процесс сочинения:**\n"
        "1️⃣ Выбери жанр, длительность и героев\n"
        "2️⃣ Решай, кто начнёт - ты или я\n"
        "3️⃣ Пиши по 2-3 предложения, и я продолжу!\n"
        "🎤 Можешь писать текстом или говорить голосом!\n\n"
        "**Доступные жанры:**\n"
        "📚 Сказка - волшебные истории\n"
        "🗺 Приключение - путешествия и открытия\n"
        "🐉 Фэнтези - магия и драконы\n"
        "🔍 Детектив - расследования и тайны\n"
        "🚀 Научная фантастика - космос и технологии"
    )
    await message.answer(help_text, parse_mode="Markdown")
    logger.info(f"Command: /help, chat_id={chat_id}, user={username}")
