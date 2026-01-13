import logging
from datetime import datetime
from typing import TypedDict

from config import config

logger = logging.getLogger(__name__)


class Session(TypedDict):
    """Структура сессии пользователя"""
    messages: list[dict[str, str]]
    created_at: datetime
    last_activity: datetime


# Глобальное хранилище сессий
_sessions: dict[int, Session] = {}


def get_session(chat_id: int) -> Session:
    """Получить сессию по chat_id (создает новую если не существует)"""
    if chat_id not in _sessions:
        logger.info(f"Creating new session for chat_id: {chat_id}")
        _sessions[chat_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
        }
    return _sessions[chat_id]


def add_message(chat_id: int, role: str, content: str) -> None:
    """Добавить сообщение в историю"""
    session = get_session(chat_id)
    session["messages"].append({"role": role, "content": content})
    session["last_activity"] = datetime.now()
    
    # Ограничение истории
    max_messages = config["max_history_messages"]
    if len(session["messages"]) > max_messages:
        removed = len(session["messages"]) - max_messages
        session["messages"] = session["messages"][-max_messages:]
        logger.info(f"Trimmed {removed} old messages for chat_id: {chat_id}")


def get_messages(chat_id: int) -> list[dict[str, str]]:
    """Получить историю сообщений"""
    session = get_session(chat_id)
    return session["messages"]


def clear_session(chat_id: int) -> None:
    """Очистить историю сообщений для chat_id"""
    if chat_id in _sessions:
        logger.info(f"Clearing session for chat_id: {chat_id}")
        _sessions[chat_id]["messages"] = []
        _sessions[chat_id]["last_activity"] = datetime.now()
    else:
        logger.info(f"No session to clear for chat_id: {chat_id}")
