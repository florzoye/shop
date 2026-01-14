"""
Миграция: Добавление колонки photo_id в таблицу products
"""
import asyncio
import aiosqlite
import os


async def migrate_add_photo_column():
    """Добавляет колонку photo_id в таблицу products"""
    
    db_path = os.getenv('DATABASE_PATH', 'products.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Файл {db_path} не найден")
        return
    
    print(f"📦 Работаю с базой: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        # Проверяем существование таблицы
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
        )
        table_exists = await cursor.fetchone()
        
        if not table_exists:
            print("❌ Таблица products не найдена")
            return
        
        # Проверяем структуру таблицы
        cursor = await db.execute("PRAGMA table_info(products)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📊 Текущие колонки: {', '.join(column_names)}")
        
        # Проверяем есть ли уже photo_id
        if 'photo_id' in column_names:
            print("✅ Колонка photo_id уже существует!")
            return
        
        print("🔄 Добавляю колонку photo_id...")
        
        try:
            # Добавляем колонку
            await db.execute(
                "ALTER TABLE products ADD COLUMN photo_id TEXT"
            )
            await db.commit()
            
            print("✅ Колонка photo_id успешно добавлена!")
            
            # Проверяем результат
            cursor = await db.execute("PRAGMA table_info(products)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"📊 Новые колонки: {', '.join(column_names)}")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении колонки: {e}")
            return


if __name__ == "__main__":
    print("🚀 Миграция: добавление photo_id")
    print("=" * 50)
    asyncio.run(migrate_add_photo_column())
    print("=" * 50)
    print("✅ Готово! Перезапустите бота.")