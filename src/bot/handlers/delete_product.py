from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.config import bot_config
from src.bot.models.base import ProductCategory
from src.bot.utils.logger import setup_logger

from db.crud import BrandsSQL, ProductsSQL


router = Router()
logger = setup_logger("delete_product")


class DeleteProductStates(StatesGroup):
    selecting_category = State()
    selecting_brand = State()
    selecting_product = State()
    confirming_deletion = State()


def create_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с категориями"""
    buttons = []
    
    category_emojis = {
        "снюс": "🌿",
        "поды": "📱",
        "жидкости": "💧",
        "одноразки": "🔥",
        "пластики": "🔋",
        "расходники": "🔧",
        "разное": "📦"
    }
    
    for category in ProductCategory:
        emoji = category_emojis.get(category.value, "📦")
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {category.value.capitalize()}",
                callback_data=f"del_cat:{category.value}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="del_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_brands_keyboard(brands: list) -> InlineKeyboardMarkup:
    """Клавиатура с брендами"""
    buttons = []
    for brand in brands:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏷 {brand.name}",
                callback_data=f"del_brand:{brand.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="del_back_to_categories")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="del_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_products_keyboard(products: list) -> InlineKeyboardMarkup:
    """Клавиатура с товарами для удаления"""
    buttons = []
    for product in products:
        text = f"{product.flavor} — {product.price}₽ ({product.quantity} шт)"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"del_prod:{product.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="del_back_to_brands")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="del_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_confirmation_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Да, удалить",
                callback_data=f"del_confirm:{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="del_cancel"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("delete"))
async def delete_start(message: Message, state: FSMContext):
    """Начало процесса удаления"""
    if message.from_user.id not in bot_config.admin_ids:
        logger.warning(f"Access denied for user {message.from_user.id}")
        return await message.answer("⛔ Нет доступа")

    logger.info(f"Admin {message.from_user.id} started deletion process")
    
    await state.set_state(DeleteProductStates.selecting_category)
    await message.answer(
        "🗑 <b>Удаление товара</b>\n\n"
        "⚠️ <b>Внимание!</b> Удаление необратимо!\n\n"
        "Выберите категорию:",
        reply_markup=create_categories_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_cat:"))
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
    await state.set_state(DeleteProductStates.selecting_brand)
    
    await callback.message.edit_text(
        f"📦 <b>Категория: {category.capitalize()}</b>\n\n"
        f"Выберите бренд:",
        reply_markup=create_brands_keyboard(brands),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "del_back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Возврат к категориям"""
    await state.set_state(DeleteProductStates.selecting_category)
    await callback.message.edit_text(
        "🗑 <b>Удаление товара</b>\n\n"
        "⚠️ <b>Внимание!</b> Удаление необратимо!\n\n"
        "Выберите категорию:",
        reply_markup=create_categories_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "del_back_to_brands")
async def back_to_brands(callback: CallbackQuery, state: FSMContext, brands_db: BrandsSQL):
    """Возврат к брендам"""
    data = await state.get_data()
    category = data.get("category")
    
    if not category:
        return await back_to_categories(callback, state)
    
    brands = await brands_db.get_brands_by_category(category)
    
    if not brands:
        return await back_to_categories(callback, state)
    
    await state.set_state(DeleteProductStates.selecting_brand)
    await callback.message.edit_text(
        f"📦 <b>Категория: {category.capitalize()}</b>\n\n"
        f"Выберите бренд:",
        reply_markup=create_brands_keyboard(brands),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_brand:"))
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
    await state.set_state(DeleteProductStates.selecting_product)
    
    await callback.message.edit_text(
        f"🏷 <b>Бренд: {brand_name}</b>\n\n"
        f"Выберите товар для удаления:",
        reply_markup=create_products_keyboard(products),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_prod:"))
async def select_product(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Выбор товара для удаления"""
    product_id = int(callback.data.split(":")[1])
    
    products = await products_db.get_all()
    product = next((p for p in products if p.id == product_id), None)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    await state.update_data(
        product_id=product_id,
        product_flavor=product.flavor,
        brand_name=product.brand_name,
        product_price=product.price,
        product_quantity=product.quantity
    )
    await state.set_state(DeleteProductStates.confirming_deletion)
    
    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"🏷 Бренд: {product.brand_name}\n"
        f"📦 Вкус: {product.flavor}\n"
        f"💰 Цена: {product.price}₽\n"
        f"📊 Остаток: {product.quantity} шт\n\n"
        f"❗️ <b>Вы уверены, что хотите удалить этот товар?</b>\n"
        f"Это действие нельзя отменить!",
        reply_markup=create_confirmation_keyboard(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_confirm:"))
async def confirm_deletion(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Подтверждение и выполнение удаления"""
    product_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    
    # Удаляем товар
    success = await products_db.delete_product(product_id)
    
    if success:
        logger.info(
            f"Product deleted: id={product_id}, "
            f"brand={data.get('brand_name')}, "
            f"flavor={data.get('product_flavor')}, "
            f"admin_id={callback.from_user.id}"
        )
        
        await callback.message.edit_text(
            f"✅ <b>Товар удалён!</b>\n\n"
            f"🏷 Бренд: {data.get('brand_name')}\n"
            f"📦 Вкус: {data.get('product_flavor')}\n"
            f"💰 Цена: {data.get('product_price')}₽\n"
            f"📊 Остаток был: {data.get('product_quantity')} шт",
            parse_mode="HTML"
        )
    else:
        logger.error(f"Failed to delete product {product_id}")
        await callback.message.edit_text(
            "❌ <b>Ошибка при удалении товара</b>\n\n"
            "Попробуйте ещё раз или обратитесь к разработчику.",
            parse_mode="HTML"
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "del_cancel")
async def cancel_deletion(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления"""
    await state.clear()
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.answer()