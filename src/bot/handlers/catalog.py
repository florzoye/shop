from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.models.base import ProductCategory
from src.bot.utils.logger import setup_logger

from db.crud import BrandsSQL, ProductsSQL


router = Router()
logger = setup_logger("catalog")

async def replace_message(
    callback: CallbackQuery,
    *,
    text: str | None = None,
    photo: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None
):
    try:
        await callback.message.delete()
    except Exception:
        pass

    if photo:
        await callback.message.answer_photo(
            photo=photo,
            caption=text or " ",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            text or " ",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )


def create_main_catalog_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура каталога"""
    buttons = [
        [InlineKeyboardButton(
            text="📦 Все товары",
            callback_data="catalog_all"
        )],
        [InlineKeyboardButton(
            text="📂 По категориям",
            callback_data="catalog_categories"
        )],
        [InlineKeyboardButton(
            text="🔍 Только в наличии",
            callback_data="catalog_in_stock"
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
                callback_data=f"catalog_cat:{category.value}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="◀️ В меню", callback_data="catalog_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_brands_keyboard_catalog(brands: list, category: str) -> InlineKeyboardMarkup:
    """Клавиатура с брендами для каталога"""
    buttons = []
    for brand in brands:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏷 {brand.name}",
                callback_data=f"catalog_brand:{brand.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ К категориям", callback_data="catalog_categories")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_products_keyboard_catalog(products: list, brand_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с товарами конкретного бренда"""
    buttons = []
    for product in products:
        stock_emoji = "✅" if product.quantity > 0 else "❌"
        stock_text = f"{product.quantity} шт" if product.quantity > 0 else "нет"
        text = f"{stock_emoji} {product.flavor} — {product.price}₽ ({stock_text})"
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"catalog_prod:{product.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ К брендам", callback_data="catalog_back_to_brands")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_product_info(product, show_full: bool = True) -> str:
    """Форматирование информации о товаре"""
    stock_emoji = "✅" if product.quantity > 0 else "❌"
    stock_text = f"{product.quantity} шт" if product.quantity > 0 else "нет в наличии"
    
    if show_full:
        return (
            f"{stock_emoji} <b>{product.brand_name} - {product.flavor}</b>\n"
            f"├ Категория: {product.category.value if product.category else 'N/A'}\n"
            f"├ Цена: <b>{product.price}₽</b>\n"
            f"└ Остаток: {stock_text}"
        )
    else:
        return f"{stock_emoji} <b>{product.brand_name} - {product.flavor}</b> — {product.price}₽ ({stock_text})"


def create_pagination_keyboard(
    current_page: int,
    total_pages: int,
    prefix: str = "catalog"
) -> InlineKeyboardMarkup:
    """Клавиатура с пагинацией"""
    buttons = []
    
    # Кнопки навигации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"{prefix}_page:{current_page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="catalog_noop"
        )
    )
    
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"{prefix}_page:{current_page+1}")
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Кнопка назад
    buttons.append([
        InlineKeyboardButton(text="◀️ В меню", callback_data="catalog_back")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("catalog"))
async def catalog_start(message: Message):
    """Начало просмотра каталога"""
    logger.info(f"User {message.from_user.id} opened catalog")
    
    await message.answer(
        "🛍 <b>Каталог товаров</b>\n\n"
        "Выберите способ просмотра:",
        reply_markup=create_main_catalog_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "catalog_back")
async def catalog_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await replace_message(
        callback,
        text=(
            "🛍 <b>Каталог товаров</b>\n\n"
            "Выберите способ просмотра:"
        ),
        reply_markup=create_main_catalog_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "catalog_categories")
async def show_categories(callback: CallbackQuery):
    await replace_message(
        callback,
        text="📂 <b>Выберите категорию:</b>",
        reply_markup=create_categories_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("catalog_cat:"))
async def show_category_brands(
    callback: CallbackQuery,
    state: FSMContext,
    brands_db: BrandsSQL
):
    category = callback.data.split(":")[1]
    brands = await brands_db.get_brands_by_category(category)

    if not brands:
        await callback.answer(
            f"📭 В категории '{category}' нет брендов",
            show_alert=True
        )
        return

    await state.update_data(
        current_category=category,
        view_mode=f"category_brands:{category}"
    )

    await replace_message(
        callback,
        text=(
            f"📂 <b>Категория: {category.capitalize()}</b>\n\n"
            f"Выберите бренд ({len(brands)} шт):"
        ),
        reply_markup=create_brands_keyboard_catalog(brands, category)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("catalog_brand:"))
async def show_brand_products(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    brand_id = int(callback.data.split(":")[1])
    products = await products_db.get_products_by_brand(brand_id)

    if not products:
        await callback.answer("📭 У этого бренда нет товаров", show_alert=True)
        return

    brand_name = products[0].brand_name
    category = products[0].category.value if products[0].category else "N/A"

    await state.update_data(
        current_brand_id=brand_id,
        current_brand_name=brand_name,
        view_mode=f"brand_products:{brand_id}"
    )

    text = (
        f"🏷 <b>{brand_name}</b>\n"
        f"📂 Категория: {category}\n"
        f"📊 Всего товаров: {len(products)}"
    )

    await replace_message(
        callback,
        text=text,
        reply_markup=create_products_keyboard_catalog(products, brand_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("catalog_prod:"))
async def show_product_details(
    callback: CallbackQuery,
    state: FSMContext,
    products_db: ProductsSQL
):
    product_id = int(callback.data.split(":")[1])
    products = await products_db.get_all()

    product = next((p for p in products if p.id == product_id), None)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    stock_emoji = "✅" if product.quantity > 0 else "❌"
    stock_text = f"{product.quantity} шт" if product.quantity > 0 else "нет в наличии"

    details = (
        f"{stock_emoji} <b>{product.brand_name} - {product.flavor}</b>\n\n"
        f"📂 Категория: {product.category.value if product.category else 'N/A'}\n"
        f"🏷 Бренд: {product.brand_name}\n"
        f"💰 Цена: {product.price}₽\n"
        f"📊 Остаток: {stock_text}"
    )

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="◀️ К товарам",
            callback_data=f"catalog_brand:{product.brand_id}"
        )]
    ])

    await replace_message(
        callback,
        text=details,
        photo=product.photo_id,
        reply_markup=back_keyboard
    )
    await callback.answer()



@router.callback_query(F.data == "catalog_back_to_brands")
async def back_to_brands_catalog(
    callback: CallbackQuery,
    state: FSMContext,
    brands_db: BrandsSQL
):
    """Возврат к списку брендов"""
    data = await state.get_data()
    category = data.get("current_category")
    
    if not category:
        return await show_categories(callback)
    
    brands = await brands_db.get_brands_by_category(category)
    
    if not brands:
        return await show_categories(callback)
    
    await callback.message.edit_text(
        f"📂 <b>Категория: {category.capitalize()}</b>\n\n"
        f"Выберите бренд ({len(brands)} шт):",
        reply_markup=create_brands_keyboard_catalog(brands, category),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "catalog_all")
async def show_all_products(
    callback: CallbackQuery,
    products_db: ProductsSQL,
    state: FSMContext
):
    """Показать все товары"""
    products = await products_db.get_all()
    
    if not products:
        await callback.answer("📭 Каталог пуст", show_alert=True)
        return
    
    # Сохраняем список товаров в state для пагинации
    await state.update_data(
        current_products=products,
        view_mode="all"
    )
    
    await show_products_page(callback.message, products, 1, "Все товары")
    await callback.answer()


@router.callback_query(F.data == "catalog_in_stock")
async def show_in_stock(
    callback: CallbackQuery,
    products_db: ProductsSQL,
    state: FSMContext
):
    """Показать товары в наличии"""
    all_products = await products_db.get_all()
    products = [p for p in all_products if p.quantity > 0]
    
    if not products:
        await callback.answer("📭 Нет товаров в наличии", show_alert=True)
        return
    
    await state.update_data(
        current_products=products,
        view_mode="in_stock"
    )
    
    await show_products_page(callback.message, products, 1, "Товары в наличии")
    await callback.answer()


@router.callback_query(F.data.startswith("catalog_page:"))
async def handle_pagination(
    callback: CallbackQuery,
    state: FSMContext
):
    """Обработка пагинации"""
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    
    products = data.get("current_products", [])
    view_mode = data.get("view_mode", "all")
    
    if not products:
        await callback.answer("Нет данных", show_alert=True)
        return
    
    # Определяем заголовок
    if view_mode == "all":
        title = "Все товары"
    elif view_mode == "in_stock":
        title = "Товары в наличии"
    else:
        title = "Каталог"
    
    await show_products_page(callback.message, products, page, title)
    await callback.answer()


async def show_products_page(
    message: Message,
    products: list,
    page: int,
    title: str
):
    """Показать страницу товаров"""
    ITEMS_PER_PAGE = 10
    total_pages = (len(products) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    # Проверка границ
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Получаем товары для текущей страницы
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_products = products[start_idx:end_idx]
    
    # Формируем текст
    text_parts = [f"🛍 <b>{title}</b>"]
    text_parts.append(f"Всего товаров: {len(products)}\n")
    
    for i, product in enumerate(page_products, start=start_idx + 1):
        text_parts.append(f"{i}. {format_product_info(product, show_full=False)}")
    
    text = "\n".join(text_parts)
    
    # Показываем
    try:
        await message.edit_text(
            text,
            reply_markup=create_pagination_keyboard(page, total_pages),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")


@router.callback_query(F.data == "catalog_noop")
async def noop_handler(callback: CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await callback.answer()