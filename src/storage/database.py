"""CRUD операции с SQLite базой данных"""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_db_connection():
    """Получить соединение с БД"""
    from src.config import config
    db_path = config.get("db_path", "data/stories.db")
    
    # Создаем папку data если не существует
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Инициализация БД из schema.sql"""
    schema_path = Path(__file__).parent / "schema.sql"
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    
    conn = get_db_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    logger.info("Database initialized")
    
    # Применяем миграции для существующих БД
    migrate_add_author_name()


def migrate_add_author_name() -> None:
    """Добавить колонку author_name если её нет"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(stories)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "author_name" not in columns:
        cursor.execute("ALTER TABLE stories ADD COLUMN author_name TEXT")
        conn.commit()
        logger.info("Migration: added author_name column to stories table")
    
    conn.close()


def create_story(story_data: dict) -> int:
    """Создать новую историю, вернуть story_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO stories (user_id, author_name, genre, duration, main_hero, additional_heroes,
                           who_starts, creativity_level, status, content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        story_data["user_id"],
        story_data.get("author_name"),
        story_data["genre"],
        story_data["duration"],
        story_data["main_hero"],
        story_data["additional_heroes"],
        story_data["who_starts"],
        story_data["creativity_level"],
        story_data["status"],
        story_data["content"]
    ))
    
    story_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f"Created story {story_id} for user {story_data['user_id']}")
    return story_id


def update_story_content(story_id: int, content: list) -> None:
    """Обновить содержимое истории"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE stories SET content = ? WHERE id = ?",
        (json.dumps(content, ensure_ascii=False), story_id)
    )
    
    conn.commit()
    conn.close()


def complete_story(
    story_id: int,
    title: str,
    final_text: str,
    praise_text: str = None,
    cover_url: str = None
) -> None:
    """Завершить историю с похвалой и обложкой"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE stories 
        SET status = 'completed', title = ?, final_text = ?, praise_text = ?, cover_url = ?,
            completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (title, final_text, praise_text, cover_url, story_id))
    
    conn.commit()
    conn.close()
    
    praise_status = "with praise" if praise_text else "no praise"
    cover_status = "with cover" if cover_url else "no cover"
    logger.info(f"Completed story {story_id}: {title} ({praise_status}, {cover_status})")


def abandon_story(story_id: int) -> None:
    """Пометить историю как заброшенную"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE stories SET status = 'abandoned' WHERE id = ?",
        (story_id,)
    )
    
    conn.commit()
    conn.close()
    logger.info(f"Story {story_id} marked as abandoned")


def get_active_story(user_id: int) -> Optional[dict]:
    """Получить активную историю пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM stories WHERE user_id = ? AND status = 'in_progress' ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_user_stories(user_id: int) -> list[dict]:
    """Получить все истории пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM stories WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_story_by_id(story_id: int) -> Optional[dict]:
    """Получить историю по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_all_active_stories() -> list[dict]:
    """Получить все активные истории (для восстановления при старте)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM stories WHERE status = 'in_progress'")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def delete_story(story_id: int) -> None:
    """Удалить историю и связанные файлы"""
    from pathlib import Path
    from src.config import config
    
    # Получаем данные истории перед удалением
    story = get_story_by_id(story_id)
    if not story:
        logger.warning(f"Attempted to delete non-existent story {story_id}")
        return
    
    # Удаляем связанные файлы
    images_base = Path(config.get("images_base_path", "data/images"))
    
    # Удаляем обложку если есть
    if story.get("cover_url"):
        cover_path = Path(story["cover_url"])
        if cover_path.exists():
            cover_path.unlink()
            logger.info(f"Deleted cover file: {story['cover_url']}")
    
    # Удаляем загруженное изображение если есть
    if story.get("initial_image_url"):
        image_path = Path(story["initial_image_url"])
        if image_path.exists():
            image_path.unlink()
            logger.info(f"Deleted uploaded image: {story['initial_image_url']}")
    
    # Удаляем запись из БД
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()
    
    logger.info(f"Deleted story {story_id} from database")
