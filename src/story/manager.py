"""Управление процессом сочинения историй"""
import logging
from storage.memory import get_story_session, update_story_session

logger = logging.getLogger(__name__)

# Доступные жанры
GENRES = {
    "fairy_tale": "Сказка",
    "adventure": "Приключение",
    "fantasy": "Фэнтези",
    "detective": "Детектив",
}

DURATIONS = {
    "short": "Короткая",
    "medium": "Средняя",
    "long": "Длинная",
}


def start_story_creation(chat_id: int) -> str:
    """Начать создание новой истории"""
    from storage.memory import create_story_session
    
    create_story_session(chat_id, {})
    update_story_session(chat_id, {"state": "choosing_genre", "current_limit": None})
    
    return "Давай создадим новую историю! 📖\n\nВыбери жанр:"


def process_genre_choice(chat_id: int, genre: str) -> str:
    """Обработать выбор жанра"""
    genre_name = GENRES.get(genre, "неизвестный жанр")
    
    update_story_session(chat_id, {
        "params": {"genre": genre},
        "state": "choosing_duration"
    })
    
    return f"Отлично! Жанр: {genre_name} ✨\n\nТеперь выбери длительность истории:"


def process_duration_choice(chat_id: int, duration: str) -> str:
    """Обработать выбор длительности"""
    from config import config
    
    duration_name = DURATIONS.get(duration, "неизвестная длительность")
    
    # Устанавливаем начальный лимит по выбранной длительности
    limits = {
        "short": config["max_pairs_short"],
        "medium": config["max_pairs_medium"],
        "long": config["max_pairs_long"],
    }
    initial_limit = limits.get(duration, 10)
    
    session = get_story_session(chat_id)
    session["params"]["duration"] = duration
    update_story_session(chat_id, {
        "params": session["params"],
        "state": "entering_hero_name",
        "current_limit": initial_limit
    })
    
    return f"Замечательно! Длительность: {duration_name} 📝\n\nТеперь напиши имя главного героя твоей истории:"


def process_hero_name(chat_id: int, name: str) -> str:
    """Обработать имя героя"""
    session = get_story_session(chat_id)
    session["params"]["main_hero"] = name.strip()
    update_story_session(chat_id, {
        "params": session["params"],
        "state": "choosing_who_starts"
    })
    
    return f"Отлично! Главный герой — {name} 🦸\n\nКто начнёт историю?"


def process_who_starts(chat_id: int, who: str) -> tuple[str, bool]:
    """
    Обработать выбор кто начинает
    Возвращает: (текст ответа, нужна_ли_генерация_начала_от_бота)
    """
    session = get_story_session(chat_id)
    session["params"]["who_starts"] = who
    update_story_session(chat_id, {
        "params": session["params"],
        "state": "storytelling"
    })
    
    if who == "bot":
        return ("Отлично! Начинаю историю... ✨", True)
    else:
        hero_name = session["params"]["main_hero"]
        return (f"Прекрасно! Начинай историю про {hero_name}. Напиши 2-3 предложения.", False)


def get_genre_context(genre: str) -> str:
    """Получить контекст жанра для промпта"""
    contexts = {
        "fairy_tale": "волшебная сказка с добрыми и злыми персонажами",
        "adventure": "захватывающее приключение с путешествиями",
        "fantasy": "фэнтези с магией и необычными существами",
        "detective": "детектив с расследованием и загадками",
    }
    return contexts.get(genre, "интересная история")


def count_message_pairs(content: list) -> int:
    """Подсчет пар сообщений (user + assistant = 1 пара)"""
    return len(content) // 2


def should_offer_completion(pairs_count: int, current_limit: int) -> bool:
    """Нужно ли предложить завершение истории"""
    # Предлагаем ровно по достижении текущего лимита
    return pairs_count >= current_limit


def extend_story_limit(chat_id: int) -> None:
    """Увеличить лимит истории на 3 пары"""
    session = get_story_session(chat_id)
    if session and "current_limit" in session:
        session["current_limit"] += 3
        update_story_session(chat_id, {"current_limit": session["current_limit"]})
        logger.info(f"Extended story limit for {chat_id} to {session['current_limit']}")


def get_ending_instruction(pairs_count: int, current_limit: int) -> str:
    """Получить инструкцию для подведения к концу истории"""
    remaining = current_limit - pairs_count
    
    if remaining == 1:
        # За 1 пару до конца - явно подводим к завершению
        return (
            "ВАЖНО: История подходит к концу! "
            "НЕ вводи новых персонажей, конфликтов или обстоятельств. "
            "Подведи текущий сюжет к логическому завершению. "
            "Пиши так, чтобы история могла закончиться в следующем сообщении."
        )
    elif remaining == 2:
        # За 2 пары до конца - начинаем сворачивать сюжет
        return (
            "ВАЖНО: История приближается к концу. "
            "НЕ вводи ничего нового. "
            "Начинай разрешать конфликты и подводить сюжет к завершению."
        )
    
    return ""
