import logging
from typing import List
from datetime import datetime

from db.manager import AsyncDatabaseManager
from db.schemas import (
    create_products_table_sql,
    create_sales_table_sql,
    insert_product_sql,
    insert_sale_sql,
    select_all_products_sql,
    select_products_by_category_sql,
    select_product_by_title_and_category_sql,
    select_all_sales_sql,
    select_sales_by_date_range_sql,
    update_product_quantity_sql,
    delete_product_sql,
)
from src.bot.models.base import ProductModel, SaleModel


class ProductsSQL:
    def __init__(self, db: AsyncDatabaseManager):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_tables(self) -> bool:
        try:
            await self.db.execute(create_products_table_sql())
            return True
        except Exception as e:
            self.logger.error(f"Error creating products table: {e}")
            return False

    async def add_product(self, product: ProductModel) -> bool:
        """Добавление одного товара или пополнение существующего"""
        try:
            # Проверяем существование товара
            existing = await self.get_product_by_title_and_category(
                product.title, 
                product.category
            )
            
            if existing:
                # Пополняем существующий товар
                new_quantity = existing.quantity + product.quantity
                await self.db.execute(
                    update_product_quantity_sql(),
                    {"id": existing.id, "quantity": new_quantity}
                )
                self.logger.info(
                    f"Updated product {existing.id}: "
                    f"{existing.quantity} + {product.quantity} = {new_quantity}"
                )
            else:
                # Добавляем новый товар
                await self.db.execute(
                    insert_product_sql(),
                    {
                        "title": product.title,
                        "category": product.category,
                        "quantity": product.quantity,
                        "price": product.price,
                    },
                )
                self.logger.info(f"Added new product: {product.title}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error adding product: {e}", exc_info=True)
            return False

    async def add_products_batch(self, products: List[ProductModel]) -> int:
        """Массовое добавление товаров с пополнением существующих"""
        if not products:
            return 0
            
        added_count = 0
        for product in products:
            success = await self.add_product(product)
            if success:
                added_count += 1
        
        self.logger.info(f"Batch operation completed: {added_count}/{len(products)} products")
        return added_count

    async def get_all(self) -> List[ProductModel]:
        try:
            rows = await self.db.fetchall(select_all_products_sql())
            return [ProductModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching products: {e}")
            return []

    async def get_by_category(self, category: str) -> List[ProductModel]:
        try:
            rows = await self.db.fetchall(
                select_products_by_category_sql(),
                {"category": category},
            )
            return [ProductModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching category {category}: {e}")
            return []

    async def get_product_by_title_and_category(
        self, 
        title: str, 
        category: str
    ) -> ProductModel | None:
        """Получить товар по названию и категории"""
        try:
            row = await self.db.fetchone(
                select_product_by_title_and_category_sql(),
                {"title": title, "category": category}
            )
            if row:
                return ProductModel(**row)
            return None
        except Exception as e:
            self.logger.error(
                f"Error fetching product {title} in {category}: {e}"
            )
            return None

    async def update_quantity(self, product_id: int, quantity: int) -> bool:
        try:
            await self.db.execute(
                update_product_quantity_sql(),
                {"id": product_id, "quantity": quantity},
            )
            self.logger.info(f"Updated quantity for product {product_id} to {quantity}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error updating quantity for product {product_id}: {e}",
                exc_info=True
            )
            return False

    async def delete_product(self, product_id: int) -> bool:
        try:
            await self.db.execute(
                delete_product_sql(),
                {"id": product_id},
            )
            self.logger.info(f"Deleted product {product_id}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error deleting product {product_id}: {e}"
            )
            return False


class SalesSQL:
    def __init__(self, db: AsyncDatabaseManager):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_tables(self) -> bool:
        try:
            await self.db.execute(create_sales_table_sql())
            return True
        except Exception as e:
            self.logger.error(f"Error creating sales table: {e}")
            return False

    async def add_sale(
        self,
        product_id: int,
        admin_id: int,
        quantity: int,
        price: float
    ) -> bool:
        """Добавление продажи"""
        try:
            await self.db.execute(
                insert_sale_sql(),
                {
                    "product_id": product_id,
                    "admin_id": admin_id,
                    "quantity": quantity,
                    "price": price,
                    "sale_date": datetime.now()
                }
            )
            self.logger.info(
                f"Sale added: product_id={product_id}, quantity={quantity}, "
                f"price={price}, admin_id={admin_id}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error adding sale: {e}", exc_info=True)
            return False

    async def get_all_sales(self) -> List[SaleModel]:
        """Получить все продажи"""
        try:
            rows = await self.db.fetchall(select_all_sales_sql())
            return [SaleModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching sales: {e}")
            return []

    async def get_sales_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[SaleModel]:
        """Получить продажи за период"""
        try:
            rows = await self.db.fetchall(
                select_sales_by_date_range_sql(),
                {"start_date": start_date, "end_date": end_date}
            )
            return [SaleModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching sales by date range: {e}")
            return []