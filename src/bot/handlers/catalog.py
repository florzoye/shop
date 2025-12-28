from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from src.bot.models.base import ProductCategory
from src.bot.utils.logger import setup_logger

from db.crud import ProductsSQL


router = Router()
logger = setup_logger("catalog")


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
        "пластики": "🔋",
        "расходники": "🔧"
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
        InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_product_info(product, show_full: bool = True) -> str:
    """Форматирование информации о товаре"""
    stock_emoji = "✅" if product.quantity > 0 else "❌"
    stock_text = f"{product.quantity} шт" if product.quantity > 0 else "нет в наличии"
    
    if show_full:
        return (
            f"{stock_emoji} <b>{product.title}</b>\n"
            f"├ Категория: {product.category.value}\n"
            f"├ Цена: <b>{product.price}₽</b>\n"
            f"└ Остаток: {stock_text}"
        )
    else:
        return f"{stock_emoji} <b>{product.title}</b> — {product.price}₽ ({stock_text})"


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
async def catalog_back(callback: CallbackQuery):
    """Возврат в главное меню каталога"""
    await callback.message.edit_text(
        "🛍 <b>Каталог товаров</b>\n\n"
        "Выберите способ просмотра:",
        reply_markup=create_main_catalog_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "catalog_categories")
async def show_categories(callback: CallbackQuery):
    """Показать категории"""
    await callback.message.edit_text(
        "📂 <b>Выберите категорию:</b>",
        reply_markup=create_categories_keyboard(),
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


@router.callback_query(F.data.startswith("catalog_cat:"))
async def show_category_products(
    callback: CallbackQuery,
    products_db: ProductsSQL,
    state: FSMContext
):
    """Показать товары категории"""
    category = callback.data.split(":")[1]
    products = await products_db.get_by_category(category)
    
    if not products:
        await callback.answer(
            f"📭 В категории '{category}' нет товаров",
            show_alert=True
        )
        return
    
    await state.update_data(
        current_products=products,
        view_mode=f"category:{category}"
    )
    
    await show_products_page(
        callback.message,
        products,
        1,
        f"Категория: {category.capitalize()}"
    )
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
    elif view_mode.startswith("category:"):
        category = view_mode.split(":")[1]
        title = f"Категория: {category.capitalize()}"
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