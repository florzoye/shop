from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.bot.utils.logger import setup_logger


router = Router()
logger = setup_logger("cancel")


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    
    if current_state is None:
        logger.info(f"User {message.from_user.id} tried to cancel but no active state")
        return await message.answer(
            "ℹ️ Нет активных операций для отмены"
        )
    
    await state.clear()
    logger.info(f"User {message.from_user.id} cancelled state: {current_state}")
    
    await message.answer(
        "❌ Операция отменена\n\n"
        "Доступные команды:\n"
        "• /add_products - добавить товары\n"
        "• /sell - продать товар"
    )