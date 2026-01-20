"""Хранение состояния активных историй в памяти"""
import logging

logger = logging.getLogger(__name__)

# Глобальное хранилище сессий
_sessions: dict[int, dict] = {}


def get_story_session(chat_id: int) -> dict | None:
    """Получить активную сессию истории"""
    return _sessions.get(chat_id)


def create_story_session(chat_id: int, params: dict, story_id: int = None) -> dict:
    """Создать новую сессию истории"""
    session = {
        "chat_id": chat_id,
        "story_id": story_id,  # ID истории в БД
        "state": "choosing_genre",
        "params": params,
        "content": [],
        "is_greeted": True
    }
    _sessions[chat_id] = session
    logger.info(f"Created story session for chat_id: {chat_id}, story_id: {story_id}")
    return session


def update_story_session(chat_id: int, updates: dict) -> None:
    """Обновить сессию истории"""
    if chat_id in _sessions:
        _sessions[chat_id].update(updates)
        logger.debug(f"Updated story session for chat_id: {chat_id}")


def clear_story_session(chat_id: int) -> None:
    """Очистить сессию"""
    if chat_id in _sessions:
        _sessions.pop(chat_id)
        logger.info(f"Cleared story session for chat_id: {chat_id}")


def is_user_greeted(chat_id: int) -> bool:
    """Проверить, показано ли приветствие пользователю"""
    session = _sessions.get(chat_id)
    return session.get("is_greeted", False) if session else False


def mark_user_greeted(chat_id: int) -> None:
    """Отметить, что пользователю показано приветствие"""
    if chat_id not in _sessions:
        _sessions[chat_id] = {"is_greeted": True}
        logger.info(f"Marked user as greeted: {chat_id}")
    else:
        _sessions[chat_id]["is_greeted"] = True
