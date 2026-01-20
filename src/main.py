import asyncio
import logging
import json
from aiogram import Bot, Dispatcher

from config import config
from bot.handlers import router
from storage import database
from storage.memory import _sessions

def setup_logging() -> None:
    """Настройка логирования"""
    import os
    # Создаем папку logs если не существует
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=config["log_level"],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )

def calculate_current_limit(duration: str, content_length: int) -> int:
    """Вычислить текущий лимит с учетом уже написанного"""
    base_limits = {
        "short": config["max_pairs_short"],
        "medium": config["max_pairs_medium"],
        "long": config["max_pairs_long"],
    }
    base_limit = base_limits.get(duration, 10)
    pairs_written = content_length // 2
    
    # Если уже написано больше базового лимита - текущий лимит должен быть выше
    if pairs_written >= base_limit:
        return pairs_written + 3
    
    return base_limit


async def restore_active_stories() -> None:
    """Восстановить активные истории в память при запуске бота"""
    logger = logging.getLogger(__name__)
    
    try:
        # Инициализируем БД если нужно
        database.init_database()
        
        # Находим все активные истории
        active_stories = database.get_all_active_stories()
        
        for story in active_stories:
            user_id = story["user_id"]
            
            # Восстанавливаем сессию в памяти
            content = json.loads(story.get("content", "[]"))
            
            _sessions[user_id] = {
                "chat_id": user_id,
                "story_id": story["id"],
                "state": "storytelling",
                "params": {
                    "genre": story["genre"],
                    "duration": story["duration"],
                    "main_hero": story["main_hero"],
                    "additional_heroes": story["additional_heroes"],
                    "who_starts": story["who_starts"],
                    "creativity_level": story["creativity_level"],
                },
                "content": content,
                "current_limit": calculate_current_limit(story["duration"], len(content)),
                "is_greeted": True
            }
        
        logger.info(f"Restored {len(active_stories)} active stories")
    except Exception as e:
        logger.error(f"Error restoring active stories: {e}", exc_info=True)


async def main() -> None:
    """Основная функция запуска бота"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting bot...")
    
    # Восстанавливаем активные истории
    await restore_active_stories()
    
    bot = Bot(token=config["telegram_token"])
    dp = Dispatcher()
    
    # Регистрация обработчиков
    dp.include_router(router)
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        logger.info("Bot stopped")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())