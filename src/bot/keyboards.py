"""Клавиатуры для Telegram бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_genre_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора жанра (динамическая из genres.json)"""
    from src.story.manager import load_genres
    
    genres = load_genres()
    buttons = []
    
    for genre_id, info in genres.items():
        emoji = info.get("emoji", "📖")
        name = info["name"]
        button = InlineKeyboardButton(
            text=f"{emoji} {name}",
            callback_data=f"genre:{genre_id}"
        )
        buttons.append([button])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора длительности"""
    buttons = [
        [InlineKeyboardButton(text="⚡️ Короткая (~5 пар сообщений)", callback_data="duration:short")],
        [InlineKeyboardButton(text="📖 Средняя (~10 пар сообщений)", callback_data="duration:medium")],
        [InlineKeyboardButton(text="📚 Длинная (~20 пар сообщений)", callback_data="duration:long")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_who_starts_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора кто начинает"""
    buttons = [
        [InlineKeyboardButton(text="🤖 Начнет СочиНяшка", callback_data="starts:bot")],
        [InlineKeyboardButton(text="✍️ Ты начнёшь", callback_data="starts:user")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_creativity_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня креативности"""
    buttons = [
        [InlineKeyboardButton(
            text="😌 Спокойная история",
            callback_data="creativity:low"
        )],
        [InlineKeyboardButton(
            text="😊 Обычная история",
            callback_data="creativity:medium"
        )],
        [InlineKeyboardButton(
            text="🤩 Очень креативная!",
            callback_data="creativity:high"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_completion_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура предложения завершить историю"""
    buttons = [
        [InlineKeyboardButton(text="✅ Завершить историю", callback_data="complete:yes")],
        [InlineKeyboardButton(text="✍️ Написать ещё", callback_data="complete:no")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_story_actions_keyboard(story_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с историей"""
    buttons = [
        [InlineKeyboardButton(
            text="🗑 Удалить историю",
            callback_data=f"delete_story:{story_id}"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к списку",
            callback_data="back_to_stories"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_confirmation_keyboard(story_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    buttons = [
        [InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm_delete:{story_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"cancel_delete:{story_id}"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_image_upload_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора загрузки изображения"""
    buttons = [
        [InlineKeyboardButton(
            text="📸 Загрузить изображение",
            callback_data="image:upload"
        )],
        [InlineKeyboardButton(
            text="➡️ Пропустить",
            callback_data="image:skip"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
