from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.config import bot_config
from src.bot.models.base import ProductCategory
from src.bot.utils.logger import setup_logger

from db.crud import BrandsSQL, ProductsSQL, SalesSQL

router = Router()
logger = setup_logger("sell_product")

# ID для уведомлений о продажах
SALES_NOTIFICATION_ID = 1694304302

def create_brands_keyboard(brands: list) -> InlineKeyboardMarkup:
    """Клавиатура с брендами"""
    buttons = []
    for brand in brands:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏷 {brand.name}",
                callback_data=f"sell_brand:{brand.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="sell_back_to_categories")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="sell_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

class SellProductStates(StatesGroup):
    selecting_category = State()
    selecting_brand = State()
    selecting_product = State()
    entering_quantity = State()
    entering_price = State()


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
                callback_data=f"sell_cat:{category.value}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="sell_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_products_keyboard(products: list, category: str) -> InlineKeyboardMarkup:
    """Клавиатура с товарами (вкусами)"""
    buttons = []
    for product in products:
        stock_info = f"({product.quantity} шт)" if product.quantity > 0 else "(нет)"
        # Показываем цену в кнопке
        text = f"{product.flavor} — {product.price}₽ {stock_info}"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"sell_prod:{product.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="sell_back_to_brands")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="sell_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("sell"))
async def sell_start(message: Message, state: FSMContext):
    """Начало процесса продажи"""
    if message.from_user.id not in bot_config.admin_ids:
        logger.warning(f"Access denied for user {message.from_user.id}")
        return await message.answer("⛔ Нет доступа")

    logger.info(f"Admin {message.from_user.id} started selling process")
    
    await state.set_state(SellProductStates.selecting_category)
    await message.answer(
        "🛒 <b>Продажа товара</b>\n\n"
        "Выберите категорию товара:",
        reply_markup=create_categories_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sell_cat:"))
async def select_category(
    callback: CallbackQuery,
    state: FSMContext,
    brands_db: BrandsSQL
):
    """Выбор категории - показываем бренды"""
    category = callback.data.split(":")[1]
    
    # Получаем бренды категории
    brands = await brands_db.get_brands_by_category(category)
    
    if not brands:
        await callback.answer("⚠️ В этой категории нет брендов", show_alert=True)
        return

    await state.update_data(category=category)
    await state.set_state(SellProductStates.selecting_brand)
    
    await callback.message.edit_text(
        f"📦 <b>Категория: {category.capitalize()}</b>\n\n"
        f"Выберите бренд:",
        reply_markup=create_brands_keyboard(brands),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "sell_back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору категорий"""
    await state.set_state(SellProductStates.selecting_category)
    await callback.message.edit_text(
        "🛒 <b>Продажа товара</b>\n\n"
        "Выберите категорию товара:",
        reply_markup=create_categories_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "sell_back_to_brands")
async def back_to_brands(callback: CallbackQuery, state: FSMContext, brands_db: BrandsSQL):
    """Возврат к выбору брендов"""
    data = await state.get_data()
    category = data.get("category")
    
    if not category:
        return await back_to_categories(callback, state)
    
    brands = await brands_db.get_brands_by_category(category)
    
    if not brands:
        return await back_to_categories(callback, state)
    
    await state.set_state(SellProductStates.selecting_brand)
    await callback.message.edit_text(
        f"📦 <b>Категория: {category.capitalize()}</b>\n\n"
        f"Выберите бренд:",
        reply_markup=create_brands_keyboard(brands),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sell_brand:"))
async def select_brand(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Выбор бренда - показываем товары"""
    brand_id = int(callback.data.split(":")[1])
    
    # Получаем товары бренда
    products = await products_db.get_products_by_brand(brand_id)
    
    if not products:
        await callback.answer("⚠️ У этого бренда нет товаров", show_alert=True)
        return
    
    brand_name = products[0].brand_name if products else "Неизвестно"
    
    await state.update_data(brand_id=brand_id, brand_name=brand_name)
    await state.set_state(SellProductStates.selecting_product)
    
    await callback.message.edit_text(
        f"🏷 <b>Бренд: {brand_name}</b>\n\n"
        f"Выберите вкус:",
        reply_markup=create_products_keyboard(products, ""),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sell_prod:"))
async def select_product(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Выбор товара (вкуса)"""
    product_id = int(callback.data.split(":")[1])
    
    # Получаем данные о товаре
    products = await products_db.get_all()
    product = next((p for p in products if p.id == product_id), None)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    if product.quantity <= 0:
        await callback.answer("⚠️ Товар отсутствует на складе", show_alert=True)
        return

    await state.update_data(
        product_id=product_id,
        product_flavor=product.flavor,
        brand_name=product.brand_name,
        product_price=product.price,
        product_quantity=product.quantity
    )
    await state.set_state(SellProductStates.entering_quantity)
    
    await callback.message.edit_text(
        f"📦 <b>{product.brand_name} - {product.flavor}</b>\n\n"
        f"💰 Цена: {product.price}₽\n"
        f"📊 Остаток: {product.quantity} шт\n\n"
        f"Введите количество для продажи (1-{product.quantity}):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SellProductStates.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext):
    """Ввод количества"""
    try:
        quantity = int(message.text)
        data = await state.get_data()
        
        if quantity <= 0:
            return await message.answer("⚠️ Количество должно быть больше 0")
        
        if quantity > data['product_quantity']:
            return await message.answer(
                f"⚠️ На складе только {data['product_quantity']} шт.\n"
                f"Введите количество от 1 до {data['product_quantity']}:"
            )

        await state.update_data(sell_quantity=quantity)
        await state.set_state(SellProductStates.entering_price)
        
        suggested_price = data['product_price'] * quantity
        await message.answer(
            f"💰 Введите цену продажи (₽)\n\n"
            f"Рекомендованная: {suggested_price}₽\n"
            f"({quantity} шт × {data['product_price']}₽)"
        )

    except ValueError:
        await message.answer("⚠️ Введите корректное число")


@router.message(SellProductStates.entering_price)
async def enter_price(
    message: Message,
    state: FSMContext,
    products_db: ProductsSQL,
    sales_db: SalesSQL
):
    """Ввод цены и завершение продажи"""
    try:
        price = float(message.text.replace(",", "."))
        
        if price <= 0:
            return await message.answer("⚠️ Цена должна быть больше 0")

        data = await state.get_data()
        
        # Обновляем количество товара на складе
        new_quantity = data['product_quantity'] - data['sell_quantity']
        quantity_updated = await products_db.update_quantity(
            data['product_id'],
            new_quantity
        )
        
        if not quantity_updated:
            logger.error(f"Failed to update quantity for product {data['product_id']}")
            return await message.answer(
                "❌ Ошибка при обновлении остатка товара.\n"
                "Попробуйте ещё раз."
            )

        # Сохраняем продажу
        sale_added = await sales_db.add_sale(
            product_id=data['product_id'],
            admin_id=message.from_user.id,
            quantity=data['sell_quantity'],
            price=price
        )
        
        if not sale_added:
            logger.error(f"Failed to add sale for product {data['product_id']}")
            # Откатываем изменение количества
            await products_db.update_quantity(
                data['product_id'],
                data['product_quantity']
            )
            return await message.answer(
                "❌ Ошибка при сохранении продажи.\n"
                "Попробуйте ещё раз."
            )

        logger.info(
            f"Sale completed: product_id={data['product_id']}, "
            f"quantity={data['sell_quantity']}, price={price}, "
            f"admin_id={message.from_user.id}"
        )

        # Итоговое сообщение
        sale_summary = (
            f"✅ <b>Продажа завершена!</b>\n\n"
            f"🏷 Бренд: {data['brand_name']}\n"
            f"📦 Вкус: {data['product_flavor']}\n"
            f"📊 Количество: {data['sell_quantity']} шт\n"
            f"💰 Сумма: {price}₽\n"
            f"📉 Остаток на складе: {new_quantity} шт"
        )
        
        await message.answer(sale_summary, parse_mode="HTML")
        
        # Отправляем уведомление владельцу
        try:
            notification = (
                f"🔔 <b>Новая продажа!</b>\n\n"
                f"🏷 Бренд: {data['brand_name']}\n"
                f"📦 Товар: {data['product_flavor']}\n"
                f"📊 Количество: {data['sell_quantity']} шт\n"
                f"💰 Сумма: {price}₽\n"
                f"👤 Продавец: {message.from_user.first_name or 'Admin'}\n"
                f"📉 Остаток: {new_quantity} шт"
            )
            await message.bot.send_message(
                SALES_NOTIFICATION_ID,
                notification,
                parse_mode="HTML"
            )
            logger.info(f"Sale notification sent to {SALES_NOTIFICATION_ID}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        
        await state.clear()

    except ValueError:
        await message.answer("⚠️ Введите корректное число (например: 100 или 99.99)")
    except Exception as e:
        logger.error(f"Unexpected error in enter_price: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла непредвиденная ошибка.\n"
            "Попробуйте начать сначала с команды /sell"
        )
        await state.clear()


@router.callback_query(F.data == "sell_cancel")
async def cancel_sell(callback: CallbackQuery, state: FSMContext):
    """Отмена продажи"""
    await state.clear()
    await callback.message.edit_text("❌ Продажа отменена")
    await callback.answer()