"""Форматирование и финализация историй"""
import logging
from pathlib import Path
from llm import client

logger = logging.getLogger(__name__)


async def finalize_story(content: list, params: dict) -> dict:
    """
    Финализировать историю: генерация названия и финального текста
    
    Returns:
        {"title": "...", "final_text": "..."}
    """
    finalization_prompt = load_finalization_prompt()
    
    genre = params.get("genre", "")
    hero = params.get("main_hero", "")
    
    story_text = compile_story_text(content)
    
    messages = [
        {"role": "system", "content": finalization_prompt},
        {"role": "user", "content": f"Жанр: {genre}\nГерой: {hero}\n\nИстория:\n{story_text}"}
    ]
    
    response = await client.send_message(messages)
    
    title, final_text = parse_response(response, story_text)
    
    logger.info(f"Story finalized: title='{title}', length={len(final_text)}")
    
    return {
        "title": title,
        "final_text": final_text
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
