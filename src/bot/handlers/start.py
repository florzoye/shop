from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.config import bot_config
from src.bot.utils.logger import setup_logger


router = Router()
logger = setup_logger("start")


def create_user_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для обычных пользователей"""
    keyboard = [
        [KeyboardButton(text="🛍 Каталог")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


def create_admin_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для администраторов"""
    keyboard = [
        [KeyboardButton(text="🛍 Каталог")],
        [KeyboardButton(text="📦 Добавить товары"), KeyboardButton(text="💰 Продать")],
        [KeyboardButton(text="🗑 Удалить товар"), KeyboardButton(text="📸 Фото")],
        [KeyboardButton(text="📊 Аналитика")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Команда /start"""
    user_id = message.from_user.id
    username = message.from_user.first_name or "Пользователь"
    is_admin = user_id in bot_config.admin_ids
    
    logger.info(f"User {user_id} ({username}) started bot. Admin: {is_admin}")
    
    if is_admin:
        keyboard = create_admin_keyboard()
        welcome_text = (
            f"👋 Привет, <b>{username}</b>!\n\n"
            f"🔑 Вы вошли как администратор.\n\n"
            f"Доступные функции:\n"
            f"📦 Управление товарами\n"
            f"💰 Продажи\n"
            f"🗑 Удаление товаров\n"
            f"🛍 Просмотр каталога"
        )
    else:
        keyboard = create_user_keyboard()
        welcome_text = (
            f"👋 Привет, <b>{username}</b>!\n\n"
            f"Добро пожаловать в наш магазин! 🛍\n\n"
            f"Используйте кнопку ниже для просмотра каталога товаров."
        )
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "🛍 Каталог")
async def catalog_button(message: Message):
    """Обработка кнопки 'Каталог'"""
    from src.bot.handlers.catalog import catalog_start
    await catalog_start(message)


@router.message(F.text == "📦 Добавить товары")
async def add_products_button(message: Message, state: FSMContext):
    """Обработка кнопки 'Добавить товары'"""
    if message.from_user.id not in bot_config.admin_ids:
        return await message.answer("⛔ Нет доступа")
    
    from src.bot.handlers.add_products import add_products_help
    await add_products_help(message, state)


@router.message(F.text == "💰 Продать")
async def sell_button(message: Message, state: FSMContext):
    """Обработка кнопки 'Продать'"""
    if message.from_user.id not in bot_config.admin_ids:
        return await message.answer("⛔ Нет доступа")
    
    from src.bot.handlers.sell_products import sell_start
    await sell_start(message, state)


@router.message(F.text == "🗑 Удалить товар")
async def delete_button(message: Message, state: FSMContext):
    """Обработка кнопки 'Удалить товар'"""
    if message.from_user.id not in bot_config.admin_ids:
        return await message.answer("⛔ Нет доступа")
    
    from src.bot.handlers.delete_product import delete_start
    await delete_start(message, state)


@router.message(F.text == "📸 Фото")
async def photo_button(message: Message, state: FSMContext):
    """Обработка кнопки 'Фото'"""
    if message.from_user.id not in bot_config.admin_ids:
        return await message.answer("⛔ Нет доступа")
    
    from src.bot.handlers.manage_photo import photo_start
    await photo_start(message, state)


@router.message(F.text == "📊 Аналитика")
async def analytics_button(message: Message):
    """Обработка кнопки 'Аналитика'"""
    if message.from_user.id not in bot_config.admin_ids:
        return await message.answer("⛔ Нет доступа")
    
    from src.bot.handlers.analytics import analytics_start
    await analytics_start(message)


@router.message(Command("menu"))
async def show_menu(message: Message):
    """Показать меню"""
    user_id = message.from_user.id
    is_admin = user_id in bot_config.admin_ids
    
    keyboard = create_admin_keyboard() if is_admin else create_user_keyboard()
    
    await message.answer(
        "📱 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )