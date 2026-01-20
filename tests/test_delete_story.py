"""Тесты для удаления историй"""
import pytest
from pathlib import Path
from src.storage import database, models


def test_delete_story_from_database():
    """Тест удаления истории из БД"""
    # Создаем тестовую историю
    story_data = models.create_story_dict(
        user_id=12345,
        genre="fairy_tale",
        duration="short",
        main_hero="Тестовый герой",
        who_starts="user",
        creativity_level="medium"
    )
    
    story_id = database.create_story(story_data)
    
    # Проверяем что история создана
    story = database.get_story_by_id(story_id)
    assert story is not None
    assert story["main_hero"] == "Тестовый герой"
    
    # Удаляем историю
    database.delete_story(story_id)
    
    # Проверяем что история удалена
    story = database.get_story_by_id(story_id)
    assert story is None


def test_delete_nonexistent_story():
    """Тест удаления несуществующей истории - не должно падать"""
    # Пытаемся удалить несуществующую историю
    database.delete_story(999999)
    # Не должно быть исключений


def test_delete_story_with_files():
    """Тест удаления истории с файлами"""
    from src.config import config
    
    # Создаем тестовую историю
    story_data = models.create_story_dict(
        user_id=12345,
        genre="fairy_tale",
        duration="short",
        main_hero="Тестовый герой",
        who_starts="user",
        creativity_level="medium"
    )
    
    story_id = database.create_story(story_data)
    
    # Создаем тестовые файлы
    images_base = Path(config.get("images_base_path", "data/images"))
    images_base.mkdir(parents=True, exist_ok=True)
    
    cover_path = images_base / "covers"
    cover_path.mkdir(exist_ok=True)
    test_cover = cover_path / f"{story_id}_test.png"
    test_cover.write_text("test cover")
    
    uploads_path = images_base / "uploads"
    uploads_path.mkdir(exist_ok=True)
    test_upload = uploads_path / f"{story_id}_test.jpg"
    test_upload.write_text("test upload")
    
    # Обновляем историю с путями к файлам
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE stories SET cover_url = ?, initial_image_url = ? WHERE id = ?",
        (str(test_cover), str(test_upload), story_id)
    )
    conn.commit()
    conn.close()
    
    # Проверяем что файлы существуют
    assert test_cover.exists()
    assert test_upload.exists()
    
    # Удаляем историю
    database.delete_story(story_id)
    
    # Проверяем что история удалена
    story = database.get_story_by_id(story_id)
    assert story is None
    
    # Проверяем что файлы удалены
    assert not test_cover.exists()
    assert not test_upload.exists()
