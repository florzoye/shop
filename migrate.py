"""
Скрипт миграции данных из SQLite в PostgreSQL
"""
import asyncio
import aiosqlite
import asyncpg
import os
from dotenv import load_dotenv


load_dotenv()


async def migrate_data():
    """Миграция данных из SQLite в PostgreSQL"""
    
    sqlite_path = "products.db"
    postgres_url = os.getenv("DATABASE_URL")
    
    if not postgres_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found: {sqlite_path}")
        return
    
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    print(f"📂 Source: {sqlite_path}")
    print(f"🎯 Target: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")
    
    # Подключение к БД
    sqlite_conn = await aiosqlite.connect(sqlite_path)
    postgres_conn = await asyncpg.connect(postgres_url)
    
    try:
        # Миграция brands
        print("\n📦 Migrating brands...")
        cursor = await sqlite_conn.execute("SELECT id, name, category FROM brands")
        brands = await cursor.fetchall()
        
        brand_id_map = {}  # Старый ID -> Новый ID
        
        for old_id, name, category in brands:
            # Вставляем в PostgreSQL
            new_id = await postgres_conn.fetchval(
                "INSERT INTO brands (name, category) VALUES ($1, $2) "
                "ON CONFLICT (name, category) DO UPDATE SET name=EXCLUDED.name "
                "RETURNING id",
                name, category
            )
            brand_id_map[old_id] = new_id
            print(f"  ✓ {name} ({category}): {old_id} -> {new_id}")
        
        print(f"✅ Brands migrated: {len(brands)}")
        
        # Миграция products
        print("\n📦 Migrating products...")
        cursor = await sqlite_conn.execute(
            "SELECT id, brand_id, flavor, quantity, price, photo_id FROM products"
        )
        products = await cursor.fetchall()
        
        product_id_map = {}
        
        for old_id, old_brand_id, flavor, quantity, price, photo_id in products:
            new_brand_id = brand_id_map.get(old_brand_id)
            if not new_brand_id:
                print(f"  ⚠️ Brand not found for product {flavor}, skipping")
                continue
            
            new_id = await postgres_conn.fetchval(
                "INSERT INTO products (brand_id, flavor, quantity, price, photo_id) "
                "VALUES ($1, $2, $3, $4, $5) RETURNING id",
                new_brand_id, flavor, quantity, float(price), photo_id
            )
            product_id_map[old_id] = new_id
            print(f"  ✓ {flavor}: {old_id} -> {new_id}")
        
        print(f"✅ Products migrated: {len(products)}")
        
        # Миграция sales
        print("\n📦 Migrating sales...")
        cursor = await sqlite_conn.execute(
            "SELECT product_id, admin_id, quantity, price, sale_date FROM sales"
        )
        sales = await cursor.fetchall()
        
        migrated_sales = 0
        for product_id, admin_id, quantity, price, sale_date in sales:
            new_product_id = product_id_map.get(product_id)
            if not new_product_id:
                print(f"  ⚠️ Product not found for sale, skipping")
                continue
            
            await postgres_conn.execute(
                "INSERT INTO sales (product_id, admin_id, quantity, price, sale_date) "
                "VALUES ($1, $2, $3, $4, $5)",
                new_product_id, admin_id, quantity, float(price), sale_date
            )
            migrated_sales += 1
        
        print(f"✅ Sales migrated: {migrated_sales}")
        
        # Статистика
        print("\n" + "="*50)
        print("📊 Migration Summary:")
        print(f"  Brands:   {len(brands)}")
        print(f"  Products: {len(products)}")
        print(f"  Sales:    {migrated_sales}")
        print("="*50)
        print("\n✅ Migration completed successfully!")
        print("\n💡 Next steps:")
        print("  1. Verify data in PostgreSQL")
        print("  2. Update .env with DATABASE_URL")
        print("  3. Restart the bot")
        print(f"  4. Backup SQLite: mv {sqlite_path} {sqlite_path}.backup")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await sqlite_conn.close()
        await postgres_conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_data())