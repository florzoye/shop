from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import os

from src.bot.config import bot_config
from src.bot.utils.logger import setup_logger
from src.bot.utils.backup import manual_backup


router = Router()
logger = setup_logger("backup_handler")


@router.message(Command("backup"))
async def backup_command(message: Message):
    """Ручное создание бэкапа"""
    if message.from_user.id not in bot_config.admin_ids:
        logger.warning(f"Access denied for user {message.from_user.id}")
        return await message.answer("⛔ Нет доступа")

    logger.info(f"Admin {message.from_user.id} requested manual backup")
    
    # Показываем что работаем
    processing_msg = await message.answer("⏳ Создаю бэкап...")
    
    # Получаем путь к БД
    db_path = os.getenv('DATABASE_PATH', 'products.db')
    
    # Создаём и отправляем бэкап
    success = await manual_backup(message.bot, db_path, message.from_user.id)
    
    await processing_msg.delete()
    
    if success:
        await message.answer(
            "✅ <b>Бэкап создан и отправлен!</b>\n\n"
            "📁 Файл сохранён в папке backups/",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при создании бэкапа</b>\n\n"
            "Проверьте логи или попробуйте позже.",
            parse_mode="HTML"
        )