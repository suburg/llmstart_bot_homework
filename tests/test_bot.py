"""Простые тесты основных функций бота"""
import pytest
from storage.memory import (
    get_story_session,
    create_story_session,
    update_story_session,
    clear_story_session,
    is_user_greeted,
    mark_user_greeted,
)


def test_create_story_session():
    """Тест создания новой сессии истории"""
    chat_id = 999999
    session = create_story_session(chat_id, {})
    assert session is not None
    assert session["state"] == "choosing_genre"
    assert session["content"] == []
    assert session["is_greeted"] is True


def test_get_story_session():
    """Тест получения сессии истории"""
    chat_id = 999998
    create_story_session(chat_id, {"genre": "fairy_tale"})
    session = get_story_session(chat_id)
    assert session is not None
    assert session["params"]["genre"] == "fairy_tale"


def test_update_story_session():
    """Тест обновления сессии истории"""
    chat_id = 999997
    create_story_session(chat_id, {})
    update_story_session(chat_id, {"state": "storytelling", "params": {"genre": "adventure"}})
    session = get_story_session(chat_id)
    assert session["state"] == "storytelling"
    assert session["params"]["genre"] == "adventure"


def test_clear_story_session():
    """Тест очистки сессии истории"""
    chat_id = 999996
    create_story_session(chat_id, {"genre": "detective"})
    clear_story_session(chat_id)
    session = get_story_session(chat_id)
    assert session is None


def test_is_user_greeted():
    """Тест проверки приветствия пользователя"""
    chat_id = 999995
    assert is_user_greeted(chat_id) is False
    mark_user_greeted(chat_id)
    assert is_user_greeted(chat_id) is True


def test_mark_user_greeted():
    """Тест отметки о приветствии"""
    chat_id = 999994
    mark_user_greeted(chat_id)
    assert is_user_greeted(chat_id) is True


def test_story_content_tracking():
    """Тест отслеживания контента истории"""
    chat_id = 999993
    session = create_story_session(chat_id, {})
    
    # Добавляем контент
    session["content"].append({"role": "user", "content": "Жил-был герой"})
    session["content"].append({"role": "assistant", "content": "Он отправился в путешествие"})
    update_story_session(chat_id, {"content": session["content"]})
    
    # Проверяем
    updated_session = get_story_session(chat_id)
    assert len(updated_session["content"]) == 2
    assert updated_session["content"][0]["role"] == "user"
    assert updated_session["content"][1]["role"] == "assistant"
