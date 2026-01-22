"""Форматирование и финализация историй"""
import logging
from pathlib import Path
import openai
from src.ai import llm
from src.story.manager import get_temperature_for_creativity

logger = logging.getLogger(__name__)


async def finalize_story(content: list, params: dict, story_id: int = None) -> dict:
    """
    Финализировать историю: генерация названия, финального текста, обложки и похвалы
    Сохраняет результат в БД если передан story_id
    
    Returns:
        {"title": "...", "final_text": "...", "praise": "...", "cover_url": "..."}
    """
    finalization_prompt = load_finalization_prompt()
    
    genre = params.get("genre", "")
    hero = params.get("main_hero", "")
    additional = params.get("additional_heroes")
    
    story_text = compile_story_text(content)
    
    # Формируем контекст персонажей
    hero_context = f"Главный герой: {hero}"
    if additional:
        hero_context += f"\nДругие персонажи: {additional}"
    
    messages = [
        {"role": "system", "content": finalization_prompt},
        {"role": "user", "content": f"Жанр: {genre}\n{hero_context}\n\nИстория:\n{story_text}"}
    ]
    
    # Получаем температуру из параметров
    creativity = params.get("creativity_level", "medium")
    temperature = get_temperature_for_creativity(creativity)
    
    # Генерируем название и финальный текст с fallback
    try:
        response = await llm.send_message(messages, temperature=temperature)
        title, final_text = parse_response(response, story_text)
    except Exception as e:
        logger.error(f"Failed to generate title/final text: {e}")
        # Graceful fallback - используем исходный текст
        title = "Наша замечательная история"
        final_text = story_text
    
    # Генерируем персональную похвалу с fallback
    try:
        praise = await llm.generate_praise(content, params)
    except Exception as e:
        logger.error(f"Failed to generate praise: {e}")
        # Graceful fallback
        praise = "Отличная работа! Ты создал замечательную историю! 🎉"
    
    # Генерируем обложку (с graceful fallback)
    cover_url = None
    if story_id:
        cover_url = await generate_cover_safe(story_id, title, final_text, params)
    
    # Сохраняем в БД если есть story_id
    if story_id:
        from src.storage import database
        database.complete_story(story_id, title, final_text, praise, cover_url)
        cover_status = f"with cover ({cover_url})" if cover_url else "no cover"
        logger.info(f"Story {story_id} completed: title='{title}', {cover_status}")
    else:
        logger.info(f"Story finalized: title='{title}', length={len(final_text)}")
    
    return {
        "title": title,
        "final_text": final_text,
        "praise": praise,
        "cover_url": cover_url
    }


def compile_story_text(content: list) -> str:
    """Скомпилировать историю из массива сообщений в один текст"""
    parts = []
    for msg in content:
        parts.append(msg["content"])
    return " ".join(parts)


def parse_response(response: str, fallback_text: str) -> tuple[str, str]:
    """Распарсить ответ LLM на название и текст"""
    lines = response.strip().split("\n")
    
    title = ""
    final_text_lines = []
    in_text = False
    
    for line in lines:
        line_upper = line.upper().strip()
        
        if "НАЗВАНИЕ:" in line_upper:
            title = line.split(":", 1)[1].strip()
        elif "ТЕКСТ:" in line_upper:
            in_text = True
        elif in_text:
            # Сохраняем все строки включая пустые для абзацев
            final_text_lines.append(line)
    
    if not title:
        title = lines[0].strip() if lines else "Наша история"
    
    # Объединяем через перенос строки для сохранения форматирования
    final_text = "\n".join(final_text_lines).strip() if final_text_lines else fallback_text
    
    return title, final_text


def load_finalization_prompt() -> str:
    """Загрузить промпт финализации из файла"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "finalization.txt"
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Finalization prompt not found: {prompt_path}")
        return get_fallback_prompt()


def get_fallback_prompt() -> str:
    """Резервный промпт финализации"""
    return (
        "Ты редактор детских историй. На основе истории:\n"
        "1. Придумай короткое название\n"
        "2. Отформатируй текст в единое повествование\n\n"
        "Формат:\n"
        "НАЗВАНИЕ: [название]\n\n"
        "ТЕКСТ:\n[текст]"
    )


async def generate_cover_safe(
    story_id: int,
    title: str,
    final_text: str,
    params: dict
) -> str:
    """Генерация обложки с graceful fallback"""
    from src.config import config
    from src.ai import image_gen
    from src.storage import database
    
    # Проверяем наличие API ключа
    if not config.get("image_gen_api_key"):
        logger.warning("IMAGE_GEN_API_KEY not set, skipping cover generation")
        return None
    
    try:
        # Получаем референсы жанра
        genre_id = params.get("genre", "")
        references = get_genre_references(genre_id)
        
        # Получаем имя автора из БД
        story = database.get_story_by_id(story_id)
        author_name = story.get("author_name") or "Юный писатель"
        
        # Создаем краткое содержание (первые 200 символов)
        story_preview = final_text[:200].strip()
        if len(final_text) > 200:
            story_preview += "..."
        
        cover_url = await image_gen.generate_cover(
            story_id=story_id,
            title=title,
            genre=params.get("genre", ""),
            main_hero=params.get("main_hero", ""),
            author_name=author_name,
            story_preview=story_preview,
            references=references
        )
        
        return cover_url
        
    except Exception as e:
        logger.error(f"Failed to generate cover for story {story_id}: {e}")
        return None


def get_genre_references(genre_id: str) -> list[str]:
    """Получить референсы жанра из genres.json"""
    import json
    
    genres_path = Path(__file__).parent.parent.parent / "data" / "genres.json"
    
    try:
        with open(genres_path, "r", encoding="utf-8") as f:
            genres = json.load(f)
        
        genre_data = genres.get(genre_id, {})
        return genre_data.get("references", [])
        
    except Exception as e:
        logger.error(f"Failed to load genre references: {e}")
        return []
