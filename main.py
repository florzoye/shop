import asyncio
from src.bot.main import start_bot
from migrate import migrate_add_photo_column

if __name__ == "__main__":
    asyncio.run(migrate_add_photo_column())
    asyncio.run(start_bot())
