"""Тесты для работы с базой данных"""
import pytest
import tempfile
import os
from pathlib import Path

from src.storage import database, models


@pytest.fixture(scope="function", autouse=False)
def temp_db(monkeypatch):
    """Временная БД для тестов"""
    import uuid
    
    # Создаем уникальный временный файл БД для каждого теста
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"test_stories_{uuid.uuid4().hex}.db")
    
    # Патчим конфиг через monkeypatch
    from src import config
    monkeypatch.setitem(config.config, "db_path", temp_path)
    
    # Инициализируем БД
    database.init_database()
    
    yield temp_path
    
    # Очистка
    if os.path.exists(temp_path):
        try:
            os.unlink(temp_path)
        except:
            pass  # Игнорируем ошибки удаления


def test_init_database(temp_db):
    """Тест инициализации БД"""
    # Просто проверяем что БД инициализируется без ошибок
    # Файл уже должен быть создан в фикстуре
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stories'")
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None
    assert result[0] == "stories"


def test_create_story(temp_db):
    """Тест создания истории"""
    story_data = models.create_story_dict(
        user_id=123456,
        genre="fairy_tale",
        duration="short",
        main_hero="Вася",
        who_starts="bot",
        creativity_level="medium",
        additional_heroes="Петя, Маша"
    )
    
    story_id = database.create_story(story_data)
    
    assert story_id > 0
    
    # Проверяем что история создана
    story = database.get_story_by_id(story_id)
    assert story is not None
    assert story["user_id"] == 123456
    assert story["main_hero"] == "Вася"
    assert story["status"] == "in_progress"


def test_update_story_content(temp_db):
    """Тест обновления контента истории"""
    story_data = models.create_story_dict(
        user_id=123456,
        genre="adventure",
        duration="medium",
        main_hero="Герой",
        who_starts="user",
        creativity_level="high"
    )
    
    story_id = database.create_story(story_data)
    
    content = [
        {"role": "user", "content": "Жил-был герой..."},
        {"role": "assistant", "content": "Он отправился в путешествие..."}
    ]
    
    database.update_story_content(story_id, content)
    
    # Проверяем что контент обновлен
    story = database.get_story_by_id(story_id)
    import json
    saved_content = json.loads(story["content"])
    
    assert len(saved_content) == 2
    assert saved_content[0]["role"] == "user"
    assert saved_content[1]["role"] == "assistant"


def test_complete_story(temp_db):
    """Тест завершения истории"""
    story_data = models.create_story_dict(
        user_id=123456,
        genre="detective",
        duration="long",
        main_hero="Шерлок",
        who_starts="bot",
        creativity_level="low"
    )
    
    story_id = database.create_story(story_data)
    
    database.complete_story(story_id, "Тайна раскрыта", "Это была захватывающая история!")
    
    # Проверяем что история завершена
    story = database.get_story_by_id(story_id)
    assert story["status"] == "completed"
    assert story["title"] == "Тайна раскрыта"
    assert story["final_text"] == "Это была захватывающая история!"
    assert story["completed_at"] is not None


def test_abandon_story(temp_db):
    """Тест пометки истории как заброшенной"""
    story_data = models.create_story_dict(
        user_id=123456,
        genre="fantasy",
        duration="short",
        main_hero="Эльф",
        who_starts="user",
        creativity_level="medium"
    )
    
    story_id = database.create_story(story_data)
    database.abandon_story(story_id)
    
    # Проверяем что история заброшена
    story = database.get_story_by_id(story_id)
    assert story["status"] == "abandoned"


def test_get_active_story(temp_db):
    """Тест получения активной истории"""
    user_id = 999999  # Уникальный ID для изоляции
    
    # Заброшенная история
    story1_data = models.create_story_dict(
        user_id=user_id,
        genre="fairy_tale",
        duration="short",
        main_hero="Первый",
        who_starts="bot",
        creativity_level="low"
    )
    story1_id = database.create_story(story1_data)
    database.abandon_story(story1_id)
    
    # Активная история
    story2_data = models.create_story_dict(
        user_id=user_id,
        genre="adventure",
        duration="medium",
        main_hero="Второй",
        who_starts="user",
        creativity_level="high"
    )
    story2_id = database.create_story(story2_data)
    
    # Получаем активную
    active = database.get_active_story(user_id)
    
    assert active is not None
    assert active["status"] == "in_progress"
    assert active["main_hero"] == "Второй"


def test_get_user_stories(temp_db):
    """Тест получения всех историй пользователя"""
    user_id = 888888  # Уникальный ID для изоляции
    
    # Создаем несколько историй
    created_ids = []
    for i in range(3):
        story_data = models.create_story_dict(
            user_id=user_id,
            genre="fairy_tale",
            duration="short",
            main_hero=f"Герой {i}",
            who_starts="bot",
            creativity_level="medium"
        )
        sid = database.create_story(story_data)
        created_ids.append(sid)
    
    # Получаем истории только этого пользователя
    stories = database.get_user_stories(user_id)
    user_stories = [s for s in stories if s["user_id"] == user_id]
    
    assert len(user_stories) >= 3
    assert all(s["user_id"] == user_id for s in user_stories)


def test_get_all_active_stories(temp_db):
    """Тест получения всех активных историй"""
    import uuid
    # Используем очень уникальные ID для полной изоляции
    unique_prefix = int(str(uuid.uuid4().int)[:6])
    user_ids = [unique_prefix + 1, unique_prefix + 2, unique_prefix + 3]
    
    # Создаем истории для разных пользователей
    created_ids = []
    for user_id in user_ids:
        story_data = models.create_story_dict(
            user_id=user_id,
            genre="adventure",
            duration="medium",
            main_hero=f"Герой {user_id}",
            who_starts="bot",
            creativity_level="medium"
        )
        story_id = database.create_story(story_data)
        created_ids.append((user_id, story_id))
        
        # Заброшенная для второго пользователя
        if user_id == user_ids[1]:
            database.abandon_story(story_id)
    
    # Получаем активные только для наших тестовых пользователей
    active_stories = database.get_all_active_stories()
    test_active = [s for s in active_stories if s["user_id"] in user_ids]
    
    assert len(test_active) == 2
    assert all(s["status"] == "in_progress" for s in test_active)
    assert {s["user_id"] for s in test_active} == {user_ids[0], user_ids[2]}
