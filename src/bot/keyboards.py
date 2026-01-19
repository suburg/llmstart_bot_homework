"""Клавиатуры для Telegram бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_genre_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора жанра"""
    buttons = [
        [InlineKeyboardButton(text="📚 Сказка", callback_data="genre:fairy_tale")],
        [InlineKeyboardButton(text="🗺 Приключение", callback_data="genre:adventure")],
        [InlineKeyboardButton(text="🐉 Фэнтези", callback_data="genre:fantasy")],
        [InlineKeyboardButton(text="🔍 Детектив", callback_data="genre:detective")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора длительности"""
    buttons = [
        [InlineKeyboardButton(text="⚡️ Короткая (~5 пар)", callback_data="duration:short")],
        [InlineKeyboardButton(text="📖 Средняя (~10 пар)", callback_data="duration:medium")],
        [InlineKeyboardButton(text="📚 Длинная (~20 пар)", callback_data="duration:long")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_who_starts_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора кто начинает"""
    buttons = [
        [InlineKeyboardButton(text="🤖 Я начну (бот)", callback_data="starts:bot")],
        [InlineKeyboardButton(text="✍️ Ты начнёшь (я)", callback_data="starts:user")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_completion_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура предложения завершить историю"""
    buttons = [
        [InlineKeyboardButton(text="✅ Завершить историю", callback_data="complete:yes")],
        [InlineKeyboardButton(text="✍️ Написать ещё", callback_data="complete:no")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
