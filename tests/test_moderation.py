"""Тесты для модуля модерации контента"""
import pytest
from src.ai.moderation import check_content_safety


@pytest.mark.asyncio
async def test_safe_content():
    """Проверка безопасного контента - обычная детская история"""
    text = "Жил-был храбрый рыцарь, который отправился спасать принцессу от дракона."
    result = await check_content_safety(text)
    
    assert result["is_safe"] is True
    assert result["reason"] == ""


@pytest.mark.asyncio
async def test_detective_story_safe():
    """Проверка детективной истории - должна быть безопасной"""
    text = (
        "Шерлок обнаружил следы борьбы на месте преступления. "
        "Кто-то украл драгоценности из музея!"
    )
    result = await check_content_safety(text)
    
    assert result["is_safe"] is True
    assert result["reason"] == ""


@pytest.mark.asyncio
async def test_romance_safe():
    """Проверка романтической истории без сексуального подтекста"""
    text = "Принц поцеловал принцессу, и они жили долго и счастливо."
    result = await check_content_safety(text)
    
    assert result["is_safe"] is True
    assert result["reason"] == ""


@pytest.mark.asyncio
async def test_adventure_safe():
    """Проверка приключенческой истории с конфликтом"""
    text = (
        "Пираты напали на корабль! Капитан схватился за меч "
        "и бросился в бой защищать команду."
    )
    result = await check_content_safety(text)
    
    assert result["is_safe"] is True
    assert result["reason"] == ""


@pytest.mark.asyncio
async def test_explicit_sexual_content():
    """Проверка откровенного сексуального контента - должен блокироваться"""
    text = "Explicit adult sexual content that is inappropriate for children."
    result = await check_content_safety(text)
    
    # Этот тест может быть нестабильным из-за LLM
    # но в целом такой контент должен блокироваться
    assert result["is_safe"] is False
    assert len(result["reason"]) > 0


@pytest.mark.asyncio
async def test_empty_text():
    """Проверка пустого текста"""
    result = await check_content_safety("")
    
    assert result["is_safe"] is True


@pytest.mark.asyncio
async def test_fantasy_safe():
    """Проверка фэнтези истории с магией"""
    text = (
        "Волшебник взмахнул палочкой, и из неё полетели искры. "
        "Темный маг отступил, испуганный силой заклинания."
    )
    result = await check_content_safety(text)
    
    assert result["is_safe"] is True
    assert result["reason"] == ""
