"""Модуль обработчиков бота"""
from aiogram import Router

from .commands import commands_router
from .messages import messages_router

# Главный роутер, объединяющий все обработчики
router = Router()
router.include_router(commands_router)
router.include_router(messages_router)

__all__ = ["router"]
