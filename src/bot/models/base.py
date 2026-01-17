from pydantic import BaseModel
from enum import StrEnum
from datetime import datetime


class ProductCategory(StrEnum):
    snus = "снюс"
    pods = "поды"
    liquids = "жидкости"
    disposables = "одноразки"
    plastics = "пластики"
    consumables = "расходники"
    other = "разное"


class BrandModel(BaseModel):
    """Модель бренда"""
    id: int | None = None
    name: str
    category: ProductCategory


class ProductModel(BaseModel):
    """Модель товара (вкуса)"""
    id: int | None = None
    brand_id: int
    brand_name: str | None = None  # Для JOIN запросов
    category: ProductCategory | None = None  # Для JOIN запросов
    flavor: str  # Вкус
    quantity: int
    price: float
    photo_id: str | None = None  # ID фото в Telegram


class SaleModel(BaseModel):
    """Модель продажи"""
    id: int | None = None
    product_id: int
    product_flavor: str | None = None
    brand_name: str | None = None
    category: str | None = None
    admin_id: int
    quantity: int
    price: float
    sale_date: datetime