import asyncio
import os
import shutil
from datetime import datetime
from aiogram import Bot
from aiogram.types import FSInputFile
import logging

logger = logging.getLogger(__name__)

# ID для отправки бэкапов
BACKUP_RECIPIENT_ID = 1694304302


async def create_backup(db_path: str) -> str:
    """Создание бэкапа базы данных"""
    try:
        # Создаём папку для бэкапов если её нет
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Имя файла с датой и временем
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Копируем базу данных
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Backup created: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        raise


async def send_backup(bot: Bot, backup_path: str, recipient_id: int = None):
    """Отправка бэкапа в Telegram"""
    try:
        if recipient_id is None:
            recipient_id = BACKUP_RECIPIENT_ID
            
        # Получаем размер файла
        file_size = os.path.getsize(backup_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Формируем сообщение
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        caption = (
            f"💾 <b>Автоматический бэкап БД</b>\n\n"
            f"📅 Дата: {timestamp}\n"
            f"📦 Размер: {file_size_mb:.2f} MB\n"
            f"📝 Файл: {os.path.basename(backup_path)}"
        )
        
        # Отправляем файл
        document = FSInputFile(backup_path)
        await bot.send_document(
            chat_id=recipient_id,
            document=document,
            caption=caption,
            parse_mode="HTML"
        )
        
        logger.info(f"Backup sent to {recipient_id}")
        
    except Exception as e:
        logger.error(f"Error sending backup: {e}", exc_info=True)
        raise


async def cleanup_old_backups(max_backups: int = 10):
    """Удаление старых бэкапов, оставляем только последние N"""
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return
        
        # Получаем список всех бэкапов
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith("backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                backups.append((filepath, os.path.getmtime(filepath)))
        
        # Сортируем по времени создания (новые первые)
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # Удаляем старые
        deleted_count = 0
        for filepath, _ in backups[max_backups:]:
            os.remove(filepath)
            deleted_count += 1
            logger.info(f"Deleted old backup: {filepath}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backups")
            
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}", exc_info=True)


async def scheduled_backup(bot: Bot, db_path: str):
    """Периодический бэкап каждые 12 часов"""
    # Небольшая задержка перед первым бэкапом
    await asyncio.sleep(60)
    
    while True:
        try:
            logger.info("Starting scheduled backup...")
            
            # Создаём бэкап
            backup_path = await create_backup(db_path)
            
            # Отправляем в Telegram
            await send_backup(bot, backup_path)
            
            # Очищаем старые бэкапы (храним последние 10)
            await cleanup_old_backups(max_backups=10)
            
            logger.info("✅ Scheduled backup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled backup: {e}", exc_info=True)
            
            # Отправляем уведомление об ошибке
            try:
                await bot.send_message(
                    chat_id=BACKUP_RECIPIENT_ID,
                    text=f"⚠️ <b>Ошибка при создании бэкапа!</b>\n\n{str(e)}",
                    parse_mode="HTML"
                )
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")
        
        # Ждём 12 часов (43200 секунд)
        logger.info("Next backup in 12 hours...")
        await asyncio.sleep(43200)


async def manual_backup(bot: Bot, db_path: str, user_id: int):
    """Ручной бэкап по команде"""
    try:
        # Создаём бэкап
        backup_path = await create_backup(db_path)
        
        # Получаем размер файла
        file_size = os.path.getsize(backup_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Формируем сообщение
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        caption = (
            f"💾 <b>Ручной бэкап БД</b>\n\n"
            f"📅 Дата: {timestamp}\n"
            f"📦 Размер: {file_size_mb:.2f} MB\n"
            f"📝 Файл: {os.path.basename(backup_path)}"
        )
        
        # Отправляем файл
        document = FSInputFile(backup_path)
        await bot.send_document(
            chat_id=user_id,
            document=document,
            caption=caption,
            parse_mode="HTML"
        )
        
        logger.info(f"Manual backup sent to {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error in manual backup: {e}", exc_info=True)
        return False