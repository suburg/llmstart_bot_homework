"""Простые тесты основных функций бота"""
import pytest
from storage.memory import get_session, add_message, clear_session, get_messages


def test_get_session_creates_new():
    """Тест создания новой сессии"""
    chat_id = 999999
    session = get_session(chat_id)
    assert session is not None
    assert len(session["messages"]) >= 1  # системный промпт


def test_add_message():
    """Тест добавления сообщения"""
    chat_id = 999998
    add_message(chat_id, "user", "Тест")
    messages = get_messages(chat_id)
    assert any(m["content"] == "Тест" for m in messages)


def test_clear_session():
    """Тест очистки сессии"""
    chat_id = 999997
    add_message(chat_id, "user", "Сообщение 1")
    add_message(chat_id, "assistant", "Ответ 1")
    clear_session(chat_id)
    messages = get_messages(chat_id)
    assert len(messages) == 1  # только системный промпт
