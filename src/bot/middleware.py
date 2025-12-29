from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для передачи БД в хендлеры"""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        brands_db = data.get("brands_db")
        products_db = data.get("products_db")
        sales_db = data.get("sales_db")
        
        if brands_db:
            data["brands_db"] = brands_db
        if products_db:
            data["products_db"] = products_db
        if sales_db:
            data["sales_db"] = sales_db
            
        return await handler(event, data)