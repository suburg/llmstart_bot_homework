import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import config
from bot.handlers import router

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

async def main() -> None:
    """Основная функция запуска бота"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting bot...")
    
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