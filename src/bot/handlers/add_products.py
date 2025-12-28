from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot.config import bot_config
from src.bot.utils.parse_product import parse_batch_products, format_product_list
from src.bot.utils.logger import setup_logger
from src.bot.utils.message import ADD_PRODUCTS_HELP

from db.crud import ProductsSQL


router = Router()
logger = setup_logger("add_products")


class AddProductsStates(StatesGroup):
    waiting_for_products = State()


@router.message(Command("add_products"))
async def add_products_help(message: Message, state: FSMContext):
    """Показываем инструкцию и ждем товары"""
    if message.from_user.id not in bot_config.admin_ids:
        logger.warning(f"Access denied for user {message.from_user.id}")
        return await message.answer("⛔ Нет доступа")

    logger.info(f"Admin {message.from_user.id} started adding products")
    
    await state.set_state(AddProductsStates.waiting_for_products)
    await message.answer(ADD_PRODUCTS_HELP, parse_mode="HTML")


@router.message(AddProductsStates.waiting_for_products, F.text)
async def add_products_batch_handler(
    message: Message,
    state: FSMContext,
    products_db: ProductsSQL
):
    """Принимаем товары и добавляем в БД"""
    
    try:
        # Показываем что обрабатываем
        processing_msg = await message.answer("⏳ Обрабатываю товары...")
        
        # Парсим товары
        products, errors = parse_batch_products(message.text)
        
        logger.info(
            f"Parsed: {len(products)} products, {len(errors)} errors "
            f"for admin {message.from_user.id}"
        )

        # Если ничего не распознали
        if not products and not errors:
            await processing_msg.delete()
            return await message.answer(
                "⚠️ Не удалось распознать товары.\n\n"
                "Проверьте формат:\n"
                "<code>категория | название | количество | цена</code>\n\n"
                "Пример:\n"
                "<code>снюс | VELO Ice Cool | 50 | 450</code>\n\n"
                "Отменить: /cancel",
                parse_mode="HTML"
            )

        # Если только ошибки
        if not products and errors:
            await processing_msg.delete()
            error_text = "\n".join(errors[:10])
            if len(errors) > 10:
                error_text += f"\n\n... и ещё {len(errors) - 10} ошибок"
            
            return await message.answer(
                f"❌ <b>Ошибки при парсинге:</b>\n\n{error_text}\n\n"
                f"Отменить: /cancel",
                parse_mode="HTML"
            )

        # Добавляем товары пачкой
        added_count = await products_db.add_products_batch(products)
        
        await processing_msg.delete()
        
        # Формируем ответ
        if added_count > 0:
            response_parts = [
                f"✅ <b>Обработано: {added_count} товаров</b>\n"
            ]
            
            # Показываем товары с информацией о пополнении
            products_preview = products[:5]
            products_text = []
            
            for p in products_preview:
                # Проверяем был ли товар пополнен
                existing = await products_db.get_product_by_title_and_category(
                    p.title, p.category
                )
                if existing:
                    products_text.append(
                        f"• <b>{p.title}</b>\n"
                        f"  └ {p.category.value} | Пополнено на {p.quantity} шт | {p.price}₽"
                    )
                else:
                    products_text.append(
                        f"• <b>{p.title}</b>\n"
                        f"  └ {p.category.value} | {p.quantity} шт | {p.price}₽"
                    )
            
            response_parts.append(f"📦 <b>Товары:</b>\n" + "\n".join(products_text))
            
            if len(products) > 5:
                response_parts.append(f"\n... и ещё {len(products) - 5} товаров")
            
            # Показываем ошибки если есть
            if errors:
                response_parts.append(f"\n⚠️ <b>Предупреждения:</b> {len(errors)}")
                error_preview = "\n".join(errors[:3])
                response_parts.append(error_preview)
                if len(errors) > 3:
                    response_parts.append(f"... и ещё {len(errors) - 3}")
            
            logger.info(
                f"Successfully added {added_count} products by admin {message.from_user.id}"
            )
            
            await message.answer("\n".join(response_parts), parse_mode="HTML")
            await state.clear()
        else:
            logger.error(
                f"Failed to add products to DB for admin {message.from_user.id}"
            )
            await message.answer(
                "❌ Не удалось добавить товары в базу данных.\n"
                "Попробуйте ещё раз или обратитесь к разработчику."
            )

    except Exception as e:
        logger.error(
            f"Unexpected error in add_products_batch_handler: {e}",
            exc_info=True
        )
        await message.answer(
            "❌ Произошла непредвиденная ошибка.\n"
            "Попробуйте ещё раз или обратитесь к разработчику."
        )
        await state.clear()