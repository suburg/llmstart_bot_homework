"""Управление процессом сочинения историй"""
import json
import logging
from pathlib import Path
from src.storage.memory import get_story_session, update_story_session

logger = logging.getLogger(__name__)

DURATIONS = {
    "short": "Короткая",
    "medium": "Средняя",
    "long": "Длинная",
}


def load_genres() -> dict:
    """Загрузить справочник жанров из data/genres.json"""
    genres_path = Path(__file__).parent.parent.parent / "data" / "genres.json"
    
    try:
        with open(genres_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Genres file not found: {genres_path}")
        # Возвращаем базовые жанры если файл не найден
        return {
            "fairy_tale": {"name": "Сказка", "emoji": "📚", 
                          "description": "Волшебные истории"},
            "adventure": {"name": "Приключение", "emoji": "🗺",
                         "description": "Захватывающие путешествия"},
            "fantasy": {"name": "Фэнтези", "emoji": "🐉",
                       "description": "Магия и волшебство"},
            "detective": {"name": "Детектив", "emoji": "🔍",
                         "description": "Расследования и тайны"},
        }


def format_genres_info() -> str:
    """Форматировать информацию о жанрах для вывода"""
    genres = load_genres()
    lines = ["Выбери жанр для своей истории:\n"]
    
    for genre_id, info in genres.items():
        emoji = info.get("emoji", "📖")
        name = info["name"]
        desc = info["description"]
        refs = info.get("references", [])
        
        lines.append(f"{emoji} **{name}**")
        lines.append(f"   {desc}")
        if refs:
            refs_str = ", ".join(refs[:3])  # Первые 3 референса
            lines.append(f"   _Например: {refs_str}_\n")
        else:
            lines.append("")
    
    return "\n".join(lines)


def start_story_creation(chat_id: int) -> tuple[str, bool]:
    """
    Начать создание новой истории
    Возвращает: (текст сообщения, была_ли_заброшена_старая_история)
    """
    from src.storage.memory import create_story_session
    from src.storage import database
    
    # Проверяем есть ли активная история
    active_story = database.get_active_story(chat_id)
    had_active = False
    
    if active_story:
        database.abandon_story(active_story["id"])
        had_active = True
        logger.info(f"Abandoned story {active_story['id']} for user {chat_id}")
    
    create_story_session(chat_id, {})
    update_story_session(chat_id, {"state": "choosing_genre", "current_limit": None})
    
    message = ""
    if had_active:
        message = "⚠️ Твоя незавершённая история сохранена. Её можно найти в /my_stories\n\n"
    
    message += "Давай создадим новую историю! 📖\n\n" + format_genres_info()
    
    return message, had_active


def process_genre_choice(chat_id: int, genre: str) -> str:
    """Обработать выбор жанра"""
    genres = load_genres()
    genre_info = genres.get(genre, {"name": "неизвестный жанр", "emoji": "📖"})
    genre_name = genre_info["name"]
    
    update_story_session(chat_id, {
        "params": {"genre": genre},
        "state": "choosing_duration"
    })
    
    return f"Отлично! Жанр: {genre_name} ✨\n\nТеперь выбери длительность истории:"


def process_duration_choice(chat_id: int, duration: str) -> str:
    """Обработать выбор длительности"""
    from src.config import config
    
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
    """Обработать имя главного героя"""
    session = get_story_session(chat_id)
    session["params"]["main_hero"] = name.strip()
    update_story_session(chat_id, {
        "params": session["params"],
        "state": "entering_additional_heroes"
    })
    
    return (
        f"Отлично! Главный герой — {name} 🦸\n\n"
        f"Хочешь добавить других персонажей?\n"
        f"Напиши их имена или отправь '-' чтобы пропустить."
    )


def process_additional_heroes(chat_id: int, text: str) -> str:
    """Обработать ввод дополнительных персонажей"""
    session = get_story_session(chat_id)
    
    # Если пользователь написал "нет" или "-" - пропускаем
    if text.lower().strip() in ["нет", "нет, спасибо", "-", "skip"]:
        session["params"]["additional_heroes"] = None
    else:
        session["params"]["additional_heroes"] = text.strip()
    
    update_story_session(chat_id, {
        "params": session["params"],
        "state": "choosing_creativity"
    })
    
    return "Отлично! 🎨\n\nТеперь выбери уровень креативности:"


def process_creativity_choice(chat_id: int, creativity: str) -> str:
    """Обработать выбор уровня креативности"""
    session = get_story_session(chat_id)
    session["params"]["creativity_level"] = creativity
    
    creativity_names = {
        "low": "Спокойная",
        "medium": "Обычная", 
        "high": "Очень креативная"
    }
    
    update_story_session(chat_id, {
        "params": session["params"],
        "state": "choosing_who_starts"
    })
    
    return f"Замечательно! Креативность: {creativity_names.get(creativity, 'Обычная')} ✨\n\nКто начнёт историю?"


def process_who_starts(chat_id: int, who: str) -> tuple[str, bool]:
    """
    Обработать выбор кто начинает
    Создает историю в БД и возвращает: (текст ответа, нужна_ли_генерация_начала_от_бота)
    """
    from src.storage import database, models
    
    session = get_story_session(chat_id)
    session["params"]["who_starts"] = who
    
    # Создаем историю в БД
    story_data = models.create_story_dict(
        user_id=chat_id,
        genre=session["params"]["genre"],
        duration=session["params"]["duration"],
        main_hero=session["params"]["main_hero"],
        who_starts=who,
        creativity_level=session["params"]["creativity_level"],
        additional_heroes=session["params"].get("additional_heroes")
    )
    
    story_id = database.create_story(story_data)
    
    update_story_session(chat_id, {
        "story_id": story_id,
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
    genres = load_genres()
    genre_info = genres.get(genre)
    
    if genre_info:
        return f"{genre_info['name'].lower()} - {genre_info['description'].lower()}"
    
    # Fallback на старые значения
    contexts = {
        "fairy_tale": "волшебная сказка с добрыми и злыми персонажами",
        "adventure": "захватывающее приключение с путешествиями",
        "fantasy": "фэнтези с магией и необычными существами",
        "detective": "детектив с расследованием и загадками",
        "sci_fi": "научная фантастика о будущем и технологиях",
    }
    return contexts.get(genre, "интересная история")


def get_temperature_for_creativity(creativity: str) -> float:
    """Получить температуру для LLM по уровню креативности"""
    from src.config import config
    
    temps = {
        "low": config["creativity_low"],
        "medium": config["creativity_medium"],
        "high": config["creativity_high"],
    }
    return temps.get(creativity, 0.7)


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
