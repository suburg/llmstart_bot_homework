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
        from llm.prompts import load_system_prompt
        
        system_prompt = load_system_prompt()
        _sessions[chat_id] = {
            "messages": [{"role": "system", "content": system_prompt}],
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
        }
    return _sessions[chat_id]


def add_message(chat_id: int, role: str, content: str) -> None:
    """Добавить сообщение в историю"""
    session = get_session(chat_id)
    session["messages"].append({"role": role, "content": content})
    session["last_activity"] = datetime.now()
    
    # Ограничение истории (но сохраняем системный промпт)
    max_messages = config["max_history_messages"]
    total_messages = len(session["messages"])
    
    if total_messages > max_messages + 1:  # +1 для системного промпта
        # Сохраняем системный промпт в начале
        system_msg = session["messages"][0]
        user_messages = session["messages"][1:]
        
        # Оставляем только последние max_messages сообщений
        kept_messages = user_messages[-max_messages:]
        session["messages"] = [system_msg] + kept_messages
        
        removed = total_messages - len(session["messages"])
        logger.info(f"Trimmed {removed} old messages for chat_id: {chat_id}")


def get_messages(chat_id: int) -> list[dict[str, str]]:
    """Получить историю сообщений"""
    session = get_session(chat_id)
    return session["messages"]


def clear_session(chat_id: int) -> None:
    """Очистить историю сообщений для chat_id (кроме системного промпта)"""
    if chat_id in _sessions:
        logger.info(f"Clearing session for chat_id: {chat_id}")
        # Сохраняем системный промпт
        system_msg = _sessions[chat_id]["messages"][0]
        _sessions[chat_id]["messages"] = [system_msg]
        _sessions[chat_id]["last_activity"] = datetime.now()
    else:
        logger.info(f"No session to clear for chat_id: {chat_id}")
