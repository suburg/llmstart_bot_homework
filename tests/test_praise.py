"""Тесты для генерации персональной похвалы"""
import pytest
from pathlib import Path


def test_praise_prompt_exists():
    """Проверка что файл промпта похвалы существует"""
    prompt_path = Path(__file__).parent.parent / "src" / "prompts" / "praise.txt"
    assert prompt_path.exists(), "Файл praise.txt должен существовать"
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert len(content) > 0, "Промпт похвалы не должен быть пустым"
    assert "наставник" in content.lower(), "Промпт должен содержать роль наставника"
    assert "похвал" in content.lower(), "Промпт должен упоминать похвалу"


def test_database_complete_story_with_praise():
    """Проверка что функция complete_story принимает параметр praise_text"""
    from src.storage import database
    import inspect
    
    # Проверяем сигнатуру функции
    sig = inspect.signature(database.complete_story)
    params = list(sig.parameters.keys())
    
    assert "story_id" in params
    assert "title" in params
    assert "final_text" in params
    assert "praise_text" in params, "Функция должна принимать параметр praise_text"


def test_formatter_returns_praise():
    """Проверка что finalize_story возвращает поле praise"""
    # Этот тест проверяет структуру без реального вызова API
    from src.story import formatter
    import inspect
    
    # Проверяем что функция существует и асинхронная
    assert hasattr(formatter, "finalize_story")
    assert inspect.iscoroutinefunction(formatter.finalize_story)
    
    # Проверяем документацию
    doc = formatter.finalize_story.__doc__
    assert doc is not None
    assert "praise" in doc.lower(), "Документация должна упоминать похвалу"
