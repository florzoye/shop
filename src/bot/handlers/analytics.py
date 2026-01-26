from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from collections import defaultdict
import io

from src.bot.config import bot_config
from src.bot.utils.logger import setup_logger

from db.crud import ProductsSQL, SalesSQL, UsersSQL

# Для графиков
try:
    import matplotlib
    matplotlib.use('Agg')  # Без GUI
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import rcParams
    
    # Настройка для русского языка
    rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


router = Router()
logger = setup_logger("analytics")


def create_analytics_keyboard() -> InlineKeyboardMarkup:
    """Главное меню аналитики"""
    buttons = [
        [InlineKeyboardButton(
            text="📊 Общая статистика",
            callback_data="analytics_general"
        )],
        [InlineKeyboardButton(
            text="💰 Финансы",
            callback_data="analytics_finance"
        )],
        [InlineKeyboardButton(
            text="📈 Графики продаж",
            callback_data="analytics_charts"
        )],
        [InlineKeyboardButton(
            text="🏆 ТОП товаров",
            callback_data="analytics_top"
        )],
        [InlineKeyboardButton(
            text="📦 Остатки на складе",
            callback_data="analytics_stock"
        )],
        [InlineKeyboardButton(
            text="👥 Пользователи",
            callback_data="analytics_users"
        )],
        [InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="analytics_close"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_period_keyboard() -> InlineKeyboardMarkup:
    """Выбор периода для графиков"""
    buttons = [
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="chart_period:today"),
            InlineKeyboardButton(text="📅 Неделя", callback_data="chart_period:week")
        ],
        [
            InlineKeyboardButton(text="📅 Месяц", callback_data="chart_period:month"),
            InlineKeyboardButton(text="📅 Всё время", callback_data="chart_period:all")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("analytics"))
async def analytics_start(message: Message):
    """Главное меню аналитики"""
    if message.from_user.id not in bot_config.admin_ids:
        logger.warning(f"Access denied for user {message.from_user.id}")
        return await message.answer("⛔ Нет доступа")

    logger.info(f"Admin {message.from_user.id} opened analytics")
    
    await message.answer(
        "📊 <b>Аналитика и статистика</b>\n\n"
        "Выберите раздел:",
        reply_markup=create_analytics_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "analytics_back")
async def analytics_back(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "📊 <b>Аналитика и статистика</b>\n\n"
        "Выберите раздел:",
        reply_markup=create_analytics_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "analytics_general")
async def show_general_stats(
    callback: CallbackQuery,
    products_db: ProductsSQL,
    sales_db: SalesSQL
):
    """Общая статистика"""
    try:
        # Получаем данные
        all_products = await products_db.get_all()
        all_sales = await sales_db.get_all_sales()
        
        # Подсчёты
        total_products = len(all_products)
        total_value = sum(p.price * p.quantity for p in all_products)
        total_items = sum(p.quantity for p in all_products)
        
        total_sales = len(all_sales)
        total_revenue = sum(s.price for s in all_sales)
        total_sold_items = sum(s.quantity for s in all_sales)
        
        # Категории
        categories = defaultdict(int)
        for p in all_products:
            if p.category:
                categories[p.category.value] += p.quantity
        
        # Бренды
        brands = len(set(p.brand_name for p in all_products if p.brand_name))
        
        # Средний чек
        avg_sale = total_revenue / total_sales if total_sales > 0 else 0
        
        text = (
            f"📊 <b>Общая статистика</b>\n\n"
            f"<b>📦 Склад:</b>\n"
            f"├ Всего товаров: {total_products}\n"
            f"├ Брендов: {brands}\n"
            f"├ Единиц на складе: {total_items}\n"
            f"└ Стоимость склада: {total_value:,.0f}₽\n\n"
            f"<b>💰 Продажи:</b>\n"
            f"├ Всего продаж: {total_sales}\n"
            f"├ Выручка: {total_revenue:,.0f}₽\n"
            f"├ Продано единиц: {total_sold_items}\n"
            f"└ Средний чек: {avg_sale:,.0f}₽\n\n"
            f"<b>📂 По категориям:</b>\n"
        )
        
        for cat, qty in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            text += f"├ {cat.capitalize()}: {qty} шт\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics_back")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in general stats: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке статистики", show_alert=True)


@router.callback_query(F.data == "analytics_finance")
async def show_finance_stats(
    callback: CallbackQuery,
    products_db: ProductsSQL,
    sales_db: SalesSQL
):
    """Финансовая статистика"""
    try:
        all_products = await products_db.get_all()
        all_sales = await sales_db.get_all_sales()
        
        # Текущая стоимость склада
        current_stock_value = sum(p.price * p.quantity for p in all_products)
        
        # Выручка всего
        total_revenue = sum(s.price for s in all_sales)
        
        # Продажи за последние периоды
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        revenue_today = sum(s.price for s in all_sales if s.sale_date >= today_start)
        revenue_week = sum(s.price for s in all_sales if s.sale_date >= week_start)
        revenue_month = sum(s.price for s in all_sales if s.sale_date >= month_start)
        
        # Ожидаемая прибыль (при продаже всего склада по текущим ценам)
        expected_profit = current_stock_value
        
        # Самая крупная продажа
        max_sale = max((s.price for s in all_sales), default=0)
        
        text = (
            f"💰 <b>Финансовая статистика</b>\n\n"
            f"<b>💵 Выручка:</b>\n"
            f"├ За сегодня: {revenue_today:,.0f}₽\n"
            f"├ За неделю: {revenue_week:,.0f}₽\n"
            f"├ За месяц: {revenue_month:,.0f}₽\n"
            f"└ Всего: {total_revenue:,.0f}₽\n\n"
            f"<b>📦 Склад:</b>\n"
            f"├ Стоимость: {current_stock_value:,.0f}₽\n"
            f"└ Ожидаемая прибыль: {expected_profit:,.0f}₽\n\n"
            f"<b>📊 Другое:</b>\n"
            f"└ Макс. продажа: {max_sale:,.0f}₽"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics_back")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in finance stats: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке статистики", show_alert=True)


@router.callback_query(F.data == "analytics_charts")
async def show_charts_menu(callback: CallbackQuery):
    """Меню выбора периода для графиков"""
    if not MATPLOTLIB_AVAILABLE:
        await callback.answer(
            "⚠️ Для графиков требуется установить matplotlib:\n"
            "pip install matplotlib",
            show_alert=True
        )
        return
    
    await callback.message.edit_text(
        "📈 <b>Графики продаж</b>\n\n"
        "Выберите период:",
        reply_markup=create_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("chart_period:"))
async def generate_chart(
    callback: CallbackQuery,
    sales_db: SalesSQL
):
    """Генерация графика продаж"""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    try:
        period = callback.data.split(":")[1]
        
        # Получаем продажи
        all_sales = await sales_db.get_all_sales()
        
        if not all_sales:
            await callback.answer("📭 Нет данных о продажах", show_alert=True)
            return
        
        # Фильтруем по периоду
        now = datetime.now()
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            title = "Продажи за сегодня"
        elif period == "week":
            start_date = now - timedelta(days=7)
            title = "Продажи за неделю"
        elif period == "month":
            start_date = now - timedelta(days=30)
            title = "Продажи за месяц"
        else:  # all
            start_date = min(s.sale_date for s in all_sales)
            title = "Продажи за всё время"
        
        filtered_sales = [s for s in all_sales if s.sale_date >= start_date]
        
        if not filtered_sales:
            await callback.answer("📭 Нет продаж за выбранный период", show_alert=True)
            return
        
        await callback.message.edit_text(
            "⏳ Генерирую график...",
            parse_mode="HTML"
        )
        
        # Создаём график
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # График 1: Выручка по дням
        sales_by_date = defaultdict(float)
        for sale in filtered_sales:
            date = sale.sale_date.date()
            sales_by_date[date] += sale.price
        
        dates = sorted(sales_by_date.keys())
        revenues = [sales_by_date[d] for d in dates]
        
        ax1.plot(dates, revenues, marker='o', linewidth=2, markersize=6, color='#2ecc71')
        ax1.fill_between(dates, revenues, alpha=0.3, color='#2ecc71')
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Выручка (₽)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        
        # График 2: Количество продаж по дням
        count_by_date = defaultdict(int)
        for sale in filtered_sales:
            date = sale.sale_date.date()
            count_by_date[date] += 1
        
        counts = [count_by_date[d] for d in dates]
        
        ax2.bar(dates, counts, color='#3498db', alpha=0.7)
        ax2.set_xlabel('Дата', fontsize=12)
        ax2.set_ylabel('Количество продаж', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        
        plt.tight_layout()
        
        # Сохраняем в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Отправляем график
        photo = BufferedInputFile(buf.read(), filename="sales_chart.png")
        
        stats_text = (
            f"📈 <b>{title}</b>\n\n"
            f"💰 Выручка: {sum(revenues):,.0f}₽\n"
            f"📊 Продаж: {sum(counts)}\n"
            f"💵 Средний чек: {sum(revenues)/sum(counts):,.0f}₽"
        )
        
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=stats_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics_charts")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error generating chart: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при создании графика", show_alert=True)


@router.callback_query(F.data == "analytics_top")
async def show_top_products(
    callback: CallbackQuery,
    sales_db: SalesSQL
):
    """ТОП проданных товаров"""
    try:
        all_sales = await sales_db.get_all_sales()
        
        if not all_sales:
            await callback.answer("📭 Нет данных о продажах", show_alert=True)
            return
        
        # Подсчёт по товарам
        product_stats = defaultdict(lambda: {"quantity": 0, "revenue": 0})
        for sale in all_sales:
            key = f"{sale.brand_name} - {sale.product_flavor}"
            product_stats[key]["quantity"] += sale.quantity
            product_stats[key]["revenue"] += sale.price
        
        # Сортировка по выручке
        top_by_revenue = sorted(
            product_stats.items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )[:10]
        
        text = "🏆 <b>ТОП-10 товаров по выручке</b>\n\n"
        
        for i, (product, stats) in enumerate(top_by_revenue, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += (
                f"{medal} <b>{product}</b>\n"
                f"   └ {stats['revenue']:,.0f}₽ ({stats['quantity']} шт)\n\n"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics_back")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in top products: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке ТОПа", show_alert=True)


@router.callback_query(F.data == "analytics_stock")
async def show_stock_status(
    callback: CallbackQuery,
    products_db: ProductsSQL
):
    """Остатки на складе"""
    try:
        all_products = await products_db.get_all()
        
        # Заканчивающиеся товары (< 10 шт)
        low_stock = [p for p in all_products if 0 < p.quantity < 10]
        out_of_stock = [p for p in all_products if p.quantity == 0]
        
        text = "📦 <b>Остатки на складе</b>\n\n"
        
        if low_stock:
            text += "<b>⚠️ Заканчиваются (&lt; 10 шт):</b>\n"
            for p in sorted(low_stock, key=lambda x: x.quantity)[:10]:
                text += f"├ {p.brand_name} - {p.flavor}: {p.quantity} шт\n"
            text += "\n"
        
        if out_of_stock:
            text += f"<b>❌ Нет в наличии ({len(out_of_stock)} шт):</b>\n"
            for p in out_of_stock[:10]:
                text += f"├ {p.brand_name} - {p.flavor}\n"
            if len(out_of_stock) > 10:
                text += f"└ ... и ещё {len(out_of_stock) - 10}\n"
        
        if not low_stock and not out_of_stock:
            text += "✅ Все товары в достаточном количестве!"
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics_back")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in stock status: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке остатков", show_alert=True)

@router.callback_query(F.data == "analytics_users")
async def show_users_analytics(
    callback: CallbackQuery,
    users_db: UsersSQL
):
    try:
        now = datetime.now()

        total = await users_db.get_total_users()
        new_today = await users_db.get_new_users_since(
            now.replace(hour=0, minute=0, second=0, microsecond=0)
        )
        new_week = await users_db.get_new_users_since(now - timedelta(days=7))
        new_month = await users_db.get_new_users_since(now - timedelta(days=30))

        active_today = await users_db.get_active_users_since(
            now.replace(hour=0, minute=0, second=0, microsecond=0)
        )
        active_week = await users_db.get_active_users_since(now - timedelta(days=7))
        active_month = await users_db.get_active_users_since(now - timedelta(days=30))

        text = (
            "👥 <b>Анализ пользователей</b>\n\n"
            f"<b>Всего:</b> {total}\n\n"

            "<b>➕ Новые:</b>\n"
            f"├ Сегодня: {new_today}\n"
            f"├ За 7 дней: {new_week}\n"
            f"└ За 30 дней: {new_month}\n\n"

            "<b>🔥 Активные:</b>\n"
            f"├ Сегодня: {active_today}\n"
            f"├ За 7 дней: {active_week}\n"
            f"└ За 30 дней: {active_month}\n"
        )

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics_back")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in users analytics: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке пользователей", show_alert=True)

@router.callback_query(F.data == "analytics_close")
async def close_analytics(callback: CallbackQuery):
    """Закрыть меню аналитики"""
    await callback.message.delete()
    await callback.answer()