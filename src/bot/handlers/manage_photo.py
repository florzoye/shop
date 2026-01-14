from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot.config import bot_config
from src.bot.models.base import ProductCategory
from src.bot.utils.logger import setup_logger

from db.crud import BrandsSQL, ProductsSQL


router = Router()
logger = setup_logger("manage_photo")


class ManagePhotoStates(StatesGroup):
    selecting_action = State()
    selecting_category = State()
    selecting_brand = State()
    selecting_product = State()
    uploading_photo = State()


def create_action_keyboard() -> InlineKeyboardMarkup:
    """Выбор действия с фото"""
    buttons = [
        [InlineKeyboardButton(
            text="📸 Добавить фото",
            callback_data="photo_add"
        )],
        [InlineKeyboardButton(
            text="🗑 Удалить фото",
            callback_data="photo_delete"
        )],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="photo_cancel"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с категориями"""
    buttons = []
    
    category_emojis = {
        "снюс": "🌿",
        "поды": "📱",
        "жидкости": "💧",
        "пластики": "🔋",
        "расходники": "🔧",
        "разное": "📦"
    }
    
    for category in ProductCategory:
        emoji = category_emojis.get(category.value, "📦")
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {category.value.capitalize()}",
                callback_data=f"photo_cat:{category.value}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="photo_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_brands_keyboard(brands: list) -> InlineKeyboardMarkup:
    """Клавиатура с брендами"""
    buttons = []
    for brand in brands:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏷 {brand.name}",
                callback_data=f"photo_brand:{brand.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="photo_back_to_categories")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="photo_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_products_keyboard(products: list, action: str) -> InlineKeyboardMarkup:
    """Клавиатура с товарами"""
    buttons = []
    for product in products:
        photo_status = "📸" if product.photo_id else "⚪️"
        text = f"{photo_status} {product.flavor} — {product.price}₽"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"photo_prod:{product.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="photo_back_to_brands")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="photo_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("photo"))
async def photo_start(message: Message, state: FSMContext):
    """Начало управления фото"""
    if message.from_user.id not in bot_config.admin_ids:
        logger.warning(f"Access denied for user {message.from_user.id}")
        return await message.answer("⛔ Нет доступа")

    logger.info(f"Admin {message.from_user.id} started photo management")
    
    await state.set_state(ManagePhotoStates.selecting_action)
    await message.answer(
        "📸 <b>Управление фото товаров</b>\n\n"
        "Выберите действие:",
        reply_markup=create_action_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("photo_add"))
async def select_add_photo(callback: CallbackQuery, state: FSMContext):
    """Выбрали добавление фото"""
    await state.update_data(action="add")
    await state.set_state(ManagePhotoStates.selecting_category)
    
    await callback.message.edit_text(
        "📸 <b>Добавление фото</b>\n\n"
        "Выберите категорию:",
        reply_markup=create_categories_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("photo_delete"))
async def select_delete_photo(callback: CallbackQuery, state: FSMContext):
    """Выбрали удаление фото"""
    await state.update_data(action="delete")
    await state.set_state(ManagePhotoStates.selecting_category)
    
    await callback.message.edit_text(
        "🗑 <b>Удаление фото</b>\n\n"
        "Выберите категорию:",
        reply_markup=create_categories_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("photo_cat:"))
async def select_category(
    callback: CallbackQuery,
    state: FSMContext,
    brands_db: BrandsSQL
):
    """Выбор категории"""
    category = callback.data.split(":")[1]
    brands = await brands_db.get_brands_by_category(category)
    
    if not brands:
        await callback.answer("⚠️ В этой категории нет брендов", show_alert=True)
        return

    await state.update_data(category=category)
    await state.set_state(ManagePhotoStates.selecting_brand)
    
    data = await state.get_data()
    action_text = "📸 Добавление" if data.get("action") == "add" else "🗑 Удаление"
    
    await callback.message.edit_text(
        f"{action_text} фото\n"
        f"📂 <b>Категория: {category.capitalize()}</b>\n\n"
        f"Выберите бренд:",
        reply_markup=create_brands_keyboard(brands),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "photo_back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Возврат к категориям"""
    await state.set_state(ManagePhotoStates.selecting_category)
    
    data = await state.get_data()
    action_text = "📸 Добавление" if data.get("action") == "add" else "🗑 Удаление"
    
    await callback.message.edit_text(
        f"{action_text} фото\n\n"
        f"Выберите категорию:",
        reply_markup=create_categories_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "photo_back_to_brands")
async def back_to_brands(
    callback: CallbackQuery,
    state: FSMContext,
    brands_db: BrandsSQL
):
    """Возврат к брендам"""
    data = await state.get_data()
    category = data.get("category")
    
    if not category:
        return await back_to_categories(callback, state)
    
    brands = await brands_db.get_brands_by_category(category)
    
    if not brands:
        return await back_to_categories(callback, state)
    
    await state.set_state(ManagePhotoStates.selecting_brand)
    
    action_text = "📸 Добавление" if data.get("action") == "add" else "🗑 Удаление"
    
    await callback.message.edit_text(
        f"{action_text} фото\n"
        f"📂 <b>Категория: {category.capitalize()}</b>\n\n"
        f"Выберите бренд:",
        reply_markup=create_brands_keyboard(brands),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("photo_brand:"))
async def select_brand(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Выбор бренда"""
    brand_id = int(callback.data.split(":")[1])
    products = await products_db.get_products_by_brand(brand_id)
    
    if not products:
        await callback.answer("⚠️ У этого бренда нет товаров", show_alert=True)
        return
    
    brand_name = products[0].brand_name if products else "Неизвестно"
    
    await state.update_data(brand_id=brand_id, brand_name=brand_name)
    await state.set_state(ManagePhotoStates.selecting_product)
    
    data = await state.get_data()
    action_text = "📸 Добавление" if data.get("action") == "add" else "🗑 Удаление"
    
    await callback.message.edit_text(
        f"{action_text} фото\n"
        f"🏷 <b>Бренд: {brand_name}</b>\n\n"
        f"Выберите товар:\n"
        f"📸 - есть фото | ⚪️ - нет фото",
        reply_markup=create_products_keyboard(products, data.get("action")),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("photo_prod:"))
async def select_product(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Выбор товара"""
    product_id = int(callback.data.split(":")[1])
    
    products = await products_db.get_all()
    product = next((p for p in products if p.id == product_id), None)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    data = await state.get_data()
    action = data.get("action")
    
    if action == "add":
        # Добавление фото
        await state.update_data(
            product_id=product_id,
            product_flavor=product.flavor,
            brand_name=product.brand_name
        )
        await state.set_state(ManagePhotoStates.uploading_photo)
        
        current_photo_text = ""
        if product.photo_id:
            current_photo_text = "\n\n⚠️ У товара уже есть фото. Новое фото заменит старое."
        
        await callback.message.edit_text(
            f"📸 <b>Добавление фото</b>\n\n"
            f"🏷 Бренд: {product.brand_name}\n"
            f"📦 Товар: {product.flavor}\n"
            f"💰 Цена: {product.price}₽{current_photo_text}\n\n"
            f"Отправьте фото товара:",
            parse_mode="HTML"
        )
        await callback.answer()
        
    elif action == "delete":
        # Удаление фото
        if not product.photo_id:
            await callback.answer("⚠️ У этого товара нет фото", show_alert=True)
            return
        
        success = await products_db.update_photo(product_id, None)
        
        if success:
            logger.info(
                f"Photo deleted: product_id={product_id}, "
                f"admin_id={callback.from_user.id}"
            )
            
            await callback.message.edit_text(
                f"✅ <b>Фото удалено!</b>\n\n"
                f"🏷 Бренд: {product.brand_name}\n"
                f"📦 Товар: {product.flavor}",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка при удалении фото</b>\n\n"
                "Попробуйте ещё раз.",
                parse_mode="HTML"
            )
        
        await state.clear()
        await callback.answer()


@router.message(ManagePhotoStates.uploading_photo, F.photo)
async def upload_photo(
    message: Message,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Загрузка фото"""
    data = await state.get_data()
    product_id = data.get("product_id")
    
    if not product_id:
        await message.answer("❌ Ошибка: товар не выбран")
        await state.clear()
        return
    
    # Получаем file_id самого большого фото
    photo = message.photo[-1]
    photo_id = photo.file_id
    
    # Сохраняем в БД
    success = await products_db.update_photo(product_id, photo_id)
    
    if success:
        logger.info(
            f"Photo added: product_id={product_id}, "
            f"photo_id={photo_id}, "
            f"admin_id={message.from_user.id}"
        )
        
        await message.answer(
            f"✅ <b>Фото добавлено!</b>\n\n"
            f"🏷 Бренд: {data.get('brand_name')}\n"
            f"📦 Товар: {data.get('product_flavor')}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Ошибка при сохранении фото</b>\n\n"
            "Попробуйте ещё раз.",
            parse_mode="HTML"
        )
    
    await state.clear()


@router.message(ManagePhotoStates.uploading_photo)
async def wrong_content_type(message: Message):
    """Неправильный тип контента"""
    await message.answer(
        "⚠️ Пожалуйста, отправьте <b>фото</b> товара.\n\n"
        "Для отмены: /cancel",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "photo_cancel")
async def cancel_photo(callback: CallbackQuery, state: FSMContext):
    """Отмена операции"""
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена")
    await callback.answer()