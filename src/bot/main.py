import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from db.crud import BrandsSQL, ProductsSQL, SalesSQL, UsersSQL
from db.manager import AsyncDatabaseManager

from src.bot.config import bot_config
from src.bot.handlers.add_products import router as add_products_router
from src.bot.handlers.sell_products import router as sell_router
from src.bot.handlers.delete_product import router as delete_router
from src.bot.handlers.manage_photo import router as photo_router
from src.bot.handlers.analytics import router as analytics_router
from src.bot.handlers.cancel import router as cancel_router
from src.bot.handlers.catalog import router as catalog_router
from src.bot.handlers.start import router as start_router
from src.bot.middleware import DatabaseMiddleware


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=bot_config.BOT_TOKEN)
dp = Dispatcher()


async def set_commands(bot: Bot):
    """Установка команд бота"""
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="catalog", description="🛍 Каталог товаров"),
        BotCommand(command="analytics", description="📊 Аналитика"),
        BotCommand(command="add_products", description="📦 Добавить товары"),
        BotCommand(command="sell", description="💰 Продать товар"),
        BotCommand(command="delete", description="🗑 Удалить товар"),
        BotCommand(command="photo", description="📸 Управление фото"),
        BotCommand(command="cancel", description="❌ Отменить операцию"),
    ]
    await bot.set_my_commands(commands)


async def init_database() -> tuple[AsyncDatabaseManager, BrandsSQL, ProductsSQL, SalesSQL, UsersSQL]:
    """Инициализация базы данных"""
    try:
        # Используем переменную окружения для пути к БД или дефолтное значение
        db_path = os.getenv('DATABASE_PATH', 'products.db')
        manager = AsyncDatabaseManager(db_path)
        
        # Проверяем и добавляем колонку photo_id если её нет
        await ensure_photo_column(manager)
        
        brands_db = BrandsSQL(manager)
        products_db = ProductsSQL(manager)
        sales_db = SalesSQL(manager)
        users_db = UsersSQL(manager)
        
        # Создаём таблицы (порядок важен из-за FK!)
        brands_created = await brands_db.create_tables()
        products_created = await products_db.create_tables()
        sales_created = await sales_db.create_tables()
        users_created = await users_db.create_tables()
        
        if brands_created and products_created and sales_created:
            logger.info("✅ Database tables created successfully")
        else:
            logger.error("❌ Failed to create database tables")
            
        return manager, brands_db, products_db, sales_db, users_db
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)
        raise


async def ensure_photo_column(manager: AsyncDatabaseManager):
    """Убеждаемся что колонка photo_id существует"""
    try:
        # Проверяем структуру таблицы
        rows = await manager.fetchall("PRAGMA table_info(products)")
        
        if rows:
            column_names = [row['name'] if isinstance(row, dict) else row[1] for row in rows]
            
            # Если колонки нет - добавляем
            if 'photo_id' not in column_names:
                logger.info("Adding photo_id column to products table...")
                await manager.execute(
                    "ALTER TABLE products ADD COLUMN photo_id TEXT"
                )
                logger.info("✅ photo_id column added successfully")
    except Exception as e:
        # Таблица ещё не существует - это нормально
        logger.debug(f"Could not check photo_id column: {e}")


async def on_startup():
    """Действия при запуске бота"""
    logger.info("🚀 Bot is starting...")
    await set_commands(bot)
    logger.info("✅ Bot commands set")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("🛑 Bot is shutting down...")
    await bot.session.close()
    logger.info("✅ Bot stopped")


async def start_bot():
    """Запуск бота"""
    try:
        # Инициализируем БД
        manager, brands_db, products_db, sales_db, users_db  = await init_database()
        
        # Передаём БД в хендлеры через middleware
        dp["brands_db"] = brands_db
        dp["products_db"] = products_db
        dp["sales_db"] = sales_db
        dp["users_db"] = users_db
        dp["db_manager"] = manager
        
        # Подключаем middleware
        dp.message.middleware(DatabaseMiddleware())
        dp.callback_query.middleware(DatabaseMiddleware())
        
        # Подключаем роутеры (порядок важен!)
        dp.include_router(start_router)      # Первым - start и menu
        dp.include_router(cancel_router)     # Вторым - отмена
        dp.include_router(catalog_router)    # Каталог
        dp.include_router(analytics_router)  # Аналитика
        dp.include_router(add_products_router)
        dp.include_router(sell_router)
        dp.include_router(delete_router)
        dp.include_router(photo_router)
        
        # Стартуем
        await on_startup()
        
        logger.info("🎉 Bot started successfully! Polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Critical error during bot startup: {e}", exc_info=True)
        raise
    finally:
        await on_shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("⚠️ Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)