"""Простые тесты основных функций бота"""
import pytest
from storage.memory import (
    get_session,
    add_message,
    clear_session,
    get_messages,
    get_system_prompt,
    set_custom_prompt,
    reset_system_prompt,
)


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


def test_get_system_prompt():
    """Тест получения системного промпта"""
    chat_id = 999996
    prompt = get_system_prompt(chat_id)
    assert prompt is not None
    assert len(prompt) > 0


def test_set_custom_prompt():
    """Тест установки кастомного промпта"""
    chat_id = 999995
    new_prompt = "Ты - тестовый ассистент"
    set_custom_prompt(chat_id, new_prompt)
    current_prompt = get_system_prompt(chat_id)
    assert current_prompt == new_prompt
    messages = get_messages(chat_id)
    assert len(messages) == 1  # история очищена


def test_reset_system_prompt():
    """Тест сброса системного промпта"""
    chat_id = 999994
    original_prompt = get_system_prompt(chat_id)
    new_prompt = "Кастомный промпт для теста"
    set_custom_prompt(chat_id, new_prompt)
    assert get_system_prompt(chat_id) == new_prompt
    reset_system_prompt(chat_id)
    reset_prompt = get_system_prompt(chat_id)
    assert reset_prompt == original_prompt


def test_clear_resets_custom_prompt():
    """Тест что clear не сбрасывает кастомный промпт сам по себе"""
    chat_id = 999993
    new_prompt = "Кастомный промпт"
    set_custom_prompt(chat_id, new_prompt)
    add_message(chat_id, "user", "Тест")
    clear_session(chat_id)
    # После clear кастомный промпт сохраняется
    assert get_system_prompt(chat_id) == new_prompt
    messages = get_messages(chat_id)
    assert len(messages) == 1
