from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        brands_db = data.get("brands_db")
        products_db = data.get("products_db")
        sales_db = data.get("sales_db")
        users_db = data.get("users_db")

        if brands_db:
            data["brands_db"] = brands_db
        if products_db:
            data["products_db"] = products_db
        if sales_db:
            data["sales_db"] = sales_db
        if users_db:
            data["users_db"] = users_db

        # 🔥 ОБНОВЛЯЕМ АКТИВНОСТЬ
        if users_db and isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
            await users_db.ensure_user(
                user.id,
                user.username,
                user.first_name
            )
            await users_db.update_activity(
                user.id,
                user.username,
                user.first_name
            )

        return await handler(event, data)
