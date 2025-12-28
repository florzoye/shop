from pydantic import BaseModel
from enum import StrEnum
from datetime import datetime


class ProductCategory(StrEnum):
    snus = "снюс"
    pods = "поды"
    liquids = "жидкости"
    plastics = "пластики"
    consumables = "расходники"


class ProductModel(BaseModel):
    id: int | None = None
    title: str
    category: ProductCategory
    quantity: int
    price: float


class SaleModel(BaseModel):
    """Модель продажи"""
    id: int | None = None
    product_id: int
    product_title: str | None = None
    product_category: str | None = None
    admin_id: int
    quantity: int
    price: float
    sale_date: datetime