from typing import List, Tuple
from src.bot.models.base import ProductModel, ProductCategory


def parse_batch_products(text: str) -> Tuple[List[ProductModel], List[str]]:
    """
    Парсит текст с товарами
    
    Формат: категория | название | количество | цена
    Пример: снюс | VELO Ice Cool Mint | 50 | 450
    
    Returns:
        Tuple[List[ProductModel], List[str]]: (список товаров, список ошибок)
    """
    if not text or not text.strip():
        return [], ["❌ Пустое сообщение"]
    
    products = []
    errors = []
    
    # Разбиваем на строки
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    if not lines:
        return [], ["❌ Не найдено ни одной строки с товаром"]
    
    for line_num, line in enumerate(lines, start=1):
        try:
            # Разбиваем по разделителю |
            parts = [part.strip() for part in line.split('|')]
            
            if len(parts) != 4:
                errors.append(
                    f"⚠️ Строка {line_num}: неверное количество полей "
                    f"(ожидается 4, получено {len(parts)})"
                )
                continue
            
            category_str, title, quantity_str, price_str = parts
            
            # Валидация категории
            category_str_lower = category_str.lower()
            valid_categories = [cat.value for cat in ProductCategory]
            
            if category_str_lower not in valid_categories:
                errors.append(
                    f"⚠️ Строка {line_num}: неизвестная категория '{category_str}'. "
                    f"Доступные: {', '.join(valid_categories)}"
                )
                continue
            
            # Преобразуем категорию
            category = ProductCategory(category_str_lower)
            
            # Валидация названия
            if not title or len(title) < 2:
                errors.append(
                    f"⚠️ Строка {line_num}: название товара слишком короткое"
                )
                continue
            
            # Валидация количества
            try:
                quantity = int(quantity_str)
                if quantity < 0:
                    errors.append(
                        f"⚠️ Строка {line_num}: количество не может быть отрицательным"
                    )
                    continue
            except ValueError:
                errors.append(
                    f"⚠️ Строка {line_num}: '{quantity_str}' не является числом"
                )
                continue
            
            # Валидация цены
            try:
                price = float(price_str.replace(',', '.'))
                if price <= 0:
                    errors.append(
                        f"⚠️ Строка {line_num}: цена должна быть больше 0"
                    )
                    continue
            except ValueError:
                errors.append(
                    f"⚠️ Строка {line_num}: '{price_str}' не является числом"
                )
                continue
            
            # Создаём товар
            product = ProductModel(
                title=title,
                category=category,
                quantity=quantity,
                price=price
            )
            products.append(product)
            
        except Exception as e:
            errors.append(f"⚠️ Строка {line_num}: неожиданная ошибка - {str(e)}")
    
    return products, errors


def format_product_list(products: List[ProductModel]) -> str:
    """Форматирует список товаров для отображения"""
    if not products:
        return "Нет товаров"
    
    lines = []
    for p in products:
        lines.append(
            f"• {p.title}\n"
            f"  └ {p.category.value} | {p.quantity} шт | {p.price}₽"
        )
    return "\n".join(lines)