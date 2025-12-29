import logging
from typing import List
from datetime import datetime

from db.manager import AsyncDatabaseManager
from db.schemas import (
    create_brands_table_sql,
    create_products_table_sql,
    create_sales_table_sql,
    insert_brand_sql,
    insert_product_sql,
    insert_sale_sql,
    select_brand_by_name_and_category_sql,
    select_brands_by_category_sql,
    select_all_brands_sql,
    select_product_by_brand_and_flavor_sql,
    select_products_by_brand_sql,
    select_all_products_sql,
    select_products_by_category_sql,
    select_all_sales_sql,
    select_sales_by_date_range_sql,
    update_product_quantity_sql,
    delete_product_sql,
    select_brand_by_id_sql
)
from src.bot.models.base import BrandModel, ProductModel, SaleModel


class BrandsSQL:
    def __init__(self, db: AsyncDatabaseManager):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_tables(self) -> bool:
        try:
            await self.db.execute(create_brands_table_sql())
            return True
        except Exception as e:
            self.logger.error(f"Error creating brands table: {e}")
            return False

    async def add_brand(self, brand: BrandModel) -> BrandModel | None:
        """Добавление бренда или получение существующего"""
        try:
            # Проверяем существование
            existing = await self.get_brand_by_name_and_category(
                brand.name, brand.category
            )
            
            if existing:
                self.logger.info(f"Brand already exists: {brand.name}")
                return existing
            
            # Добавляем новый
            await self.db.execute(
                insert_brand_sql(),
                {"name": brand.name, "category": brand.category}
            )
            
            # Получаем добавленный бренд
            added = await self.get_brand_by_name_and_category(
                brand.name, brand.category
            )
            self.logger.info(f"Added new brand: {brand.name}")
            return added
            
        except Exception as e:
            self.logger.error(f"Error adding brand: {e}", exc_info=True)
            return None

    async def get_brand_by_name_and_category(
        self, name: str, category: str
    ) -> BrandModel | None:
        """Получить бренд по имени и категории"""
        try:
            row = await self.db.fetchone(
                select_brand_by_name_and_category_sql(),
                {"name": name, "category": category}
            )
            if row:
                return BrandModel(**row)
            return None
        except Exception as e:
            self.logger.error(f"Error fetching brand: {e}")
            return None

    async def get_brands_by_category(self, category: str) -> List[BrandModel]:
        """Получить бренды категории"""
        try:
            rows = await self.db.fetchall(
                select_brands_by_category_sql(),
                {"category": category}
            )
            return [BrandModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching brands: {e}")
            return []

    async def get_all_brands(self) -> List[BrandModel]:
        """Получить все бренды"""
        try:
            rows = await self.db.fetchall(select_all_brands_sql())
            return [BrandModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching all brands: {e}")
            return []
    
    async def get_brand_by_id(self, brand_id: int) -> BrandModel | None:
        """Получить бренд по ID"""
        try:
            row = await self.db.fetchone(
                select_brand_by_id_sql(),
                {"id": brand_id}
            )
            if row:
                return BrandModel(**row)
            return None
        except Exception as e:
            self.logger.error(f"Error fetching brand by id: {e}", exc_info=True)
            return None


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
        try:
            existing = await self.get_product_by_brand_and_flavor(
                product.brand_id,
                product.flavor
            )

            if existing:
                new_quantity = existing.quantity + product.quantity
                await self.db.execute(
                    update_product_quantity_sql(),
                    {"id": existing.id, "quantity": new_quantity}
                )
            else:
                await self.db.execute(
                    insert_product_sql(),
                    {
                        "brand_id": product.brand_id,
                        "flavor": product.flavor,
                        "quantity": product.quantity,
                        "price": product.price,
                    }
                )

            return True

        except Exception:
            self.logger.error("Error adding product", exc_info=True)
            return False

    async def add_products_batch(self, products: list[ProductModel]) -> int:
        added = 0

        for product in products:
            if await self.add_product(product):
                added += 1

        self.logger.info(f"Batch: {added}/{len(products)} products")
        return added

    async def add_products_batch(self, products: List[ProductModel]) -> int:
        """Массовое добавление"""
        if not products:
            return 0
            
        added_count = 0
        for product in products:
            success = await self.add_product(product)
            if success:
                added_count += 1
        
        self.logger.info(f"Batch: {added_count}/{len(products)} products")
        return added_count

    async def get_product_by_brand_and_flavor(
        self, brand_id: int, flavor: str
    ) -> ProductModel | None:
        """Получить товар по бренду и вкусу"""
        try:
            row = await self.db.fetchone(
                select_product_by_brand_and_flavor_sql(),
                {"brand_id": brand_id, "flavor": flavor}
            )
            if row:
                return ProductModel(**row)
            return None
        except Exception as e:
            self.logger.error(f"Error fetching product: {e}")
            return None

    async def get_products_by_brand(self, brand_id: int) -> List[ProductModel]:
        """Получить товары бренда"""
        try:
            rows = await self.db.fetchall(
                select_products_by_brand_sql(),
                {"brand_id": brand_id}
            )
            return [ProductModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching products: {e}")
            return []

    async def get_all(self) -> List[ProductModel]:
        """Получить все товары"""
        try:
            rows = await self.db.fetchall(select_all_products_sql())
            return [ProductModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching products: {e}")
            return []

    async def get_by_category(self, category: str) -> List[ProductModel]:
        """Получить товары категории"""
        try:
            rows = await self.db.fetchall(
                select_products_by_category_sql(),
                {"category": category}
            )
            return [ProductModel(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error fetching category: {e}")
            return []

    async def update_quantity(self, product_id: int, quantity: int) -> bool:
        try:
            await self.db.execute(
                update_product_quantity_sql(),
                {"id": product_id, "quantity": quantity}
            )
            self.logger.info(f"Updated quantity: {product_id} -> {quantity}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating quantity: {e}", exc_info=True)
            return False

    async def delete_product(self, product_id: int) -> bool:
        try:
            await self.db.execute(
                delete_product_sql(),
                {"id": product_id}
            )
            self.logger.info(f"Deleted product {product_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting product: {e}")
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
            self.logger.info(f"Sale added: product_id={product_id}, qty={quantity}")
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
            self.logger.error(f"Error fetching sales by date: {e}")
            return []