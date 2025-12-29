from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot.config import bot_config
from src.bot.utils.parse_product import parse_batch_products, format_product_list
from src.bot.utils.logger import setup_logger
from src.bot.utils.message import ADD_PRODUCTS_HELP

from db.crud import ProductsSQL, BrandsSQL
from src.bot.models.base import ProductModel


router = Router()
logger = setup_logger("add_products")


class AddProductsStates(StatesGroup):
    waiting_for_products = State()



@router.message(Command("add_products"))
async def add_products_help(message: Message, state: FSMContext):
    if message.from_user.id not in bot_config.admin_ids:
        return await message.answer("⛔ Нет доступа")

    await state.set_state(AddProductsStates.waiting_for_products)
    await message.answer(ADD_PRODUCTS_HELP, parse_mode="HTML")


@router.message(AddProductsStates.waiting_for_products, F.text)
async def add_products_batch_handler(
    message: Message,
    state: FSMContext,
    products_db: ProductsSQL,
    brands_db: BrandsSQL,
):
    try:
        processing_msg = await message.answer("⏳ Обрабатываю товары...")

        items, errors = parse_batch_products(message.text)

        # Если ничего не распознали
        if not items and errors:
            await processing_msg.delete()
            return await message.answer(
                "❌ Ошибки:\n\n" + "\n".join(errors),
                parse_mode="HTML"
            )

        products: list[ProductModel] = []

        for brand, product in items:
            # 1️⃣ Добавляем или получаем бренд
            saved_brand = await brands_db.add_brand(brand)
            if not saved_brand:
                logger.error(f"Failed to save brand: {brand.name}")
                continue

            # 2️⃣ Проставляем brand_id
            product.brand_id = saved_brand.id

            products.append(product)

        # 3️⃣ Добавляем товары
        added_count = await products_db.add_products_batch(products)

        await processing_msg.delete()

        if added_count == 0:
            await message.answer(
                "❌ Не удалось добавить товары в базу данных"
            )
        else:
            await message.answer(
                f"✅ <b>Добавлено товаров:</b> {added_count}\n"
                f"⚠️ Предупреждений: {len(errors)}",
                parse_mode="HTML"
            )

        await state.clear()

    except Exception:
        logger.error("Unexpected error", exc_info=True)
        await message.answer(
            "❌ Непредвиденная ошибка. Обратитесь к разработчику."
        )
        await state.clear()