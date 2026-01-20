"""Модели данных для историй"""
from typing import Optional


def create_story_dict(
    user_id: int,
    genre: str,
    duration: str,
    main_hero: str,
    who_starts: str,
    creativity_level: str,
    additional_heroes: Optional[str] = None
) -> dict:
    """Создать структуру новой истории для сохранения в БД"""
    return {
        "user_id": user_id,
        "genre": genre,
        "duration": duration,
        "main_hero": main_hero,
        "additional_heroes": additional_heroes,
        "who_starts": who_starts,
        "creativity_level": creativity_level,
        "status": "in_progress",
        "content": "[]",  # JSON array
    }
