from typing import List, Tuple
from src.bot.models.base import ProductModel, ProductCategory, BrandModel


def parse_batch_products(text: str) -> Tuple[List[Tuple[BrandModel, ProductModel]], List[str]]:
    """
    Парсит текст с товарами в новом формате
    
    Формат: категория | бренд | вкус | количество | цена
    Пример: снюс | BOSHKI | Ice Mint | 50 | 450
    
    Returns:
        Tuple[List[Tuple[BrandModel, ProductModel]], List[str]]: 
        (список (бренд, товар), список ошибок)
    """
    if not text or not text.strip():
        return [], ["❌ Пустое сообщение"]
    
    items = []  # [(brand, product), ...]
    errors = []
    
    # Разбиваем на строки
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    if not lines:
        return [], ["❌ Не найдено ни одной строки с товаром"]
    
    for line_num, line in enumerate(lines, start=1):
        try:
            # Разбиваем по разделителю |
            parts = [part.strip() for part in line.split('|')]
            
            if len(parts) != 5:
                errors.append(
                    f"⚠️ Строка {line_num}: неверное количество полей "
                    f"(ожидается 5, получено {len(parts)})\n"
                    f"Формат: категория | бренд | вкус | количество | цена"
                )
                continue
            
            category_str, brand_name, flavor, quantity_str, price_str = parts
            
            # Валидация категории
            category_str_lower = category_str.lower()
            valid_categories = [cat.value for cat in ProductCategory]
            
            if category_str_lower not in valid_categories:
                errors.append(
                    f"⚠️ Строка {line_num}: неизвестная категория '{category_str}'. "
                    f"Доступные: {', '.join(valid_categories)}"
                )
                continue
            
            category = ProductCategory(category_str_lower)
            
            # Валидация бренда
            if not brand_name or len(brand_name) < 2:
                errors.append(
                    f"⚠️ Строка {line_num}: название бренда слишком короткое"
                )
                continue
            
            # Валидация вкуса
            if not flavor or len(flavor) < 2:
                errors.append(
                    f"⚠️ Строка {line_num}: название вкуса слишком короткое"
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
            
            # Создаём бренд и товар
            brand = BrandModel(
                name=brand_name,
                category=category
            )
            
            product = ProductModel(
                brand_id=0,  # Будет установлен позже
                flavor=flavor,
                quantity=quantity,
                price=price
            )
            
            items.append((brand, product))
            
        except Exception as e:
            errors.append(f"⚠️ Строка {line_num}: неожиданная ошибка - {str(e)}")
    
    return items, errors


def format_product_list(products: List[ProductModel]) -> str:
    """Форматирует список товаров для отображения"""
    if not products:
        return "Нет товаров"
    
    lines = []
    for p in products:
        lines.append(
            f"• {p.brand_name} - {p.flavor}\n"
            f"  └ {p.category.value if p.category else 'N/A'} | "
            f"{p.quantity} шт | {p.price}₽"
        )
    return "\n".join(lines)