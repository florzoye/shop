import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
@dataclass
class BotConfig:
    """Конфигурация бота"""
    BOT_TOKEN: str
    admin_ids: List[int]
    
    @classmethod
    def from_env(cls):
        """Загрузка конфигурации из переменных окружения"""
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN not found in environment variables")
        
        # Получаем список ID админов из переменной окружения
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [
            int(id.strip()) 
            for id in admin_ids_str.split(",") 
            if id.strip().isdigit()
        ]
        
        if not admin_ids:
            print("⚠️ Warning: No admin IDs configured")
        
        return cls(
            BOT_TOKEN=token,
            admin_ids=admin_ids
        )


try:
    bot_config = BotConfig.from_env()
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("💡 Please set BOT_TOKEN environment variable")
    print("💡 Example: export BOT_TOKEN='your_token_here'")
    print("💡 Example: export ADMIN_IDS='123456789,987654321'")
    exit(1)