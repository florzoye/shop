def create_brands_table_sql() -> str:
    """Таблица брендов"""
    return """
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, category)
    );
    """


def create_products_table_sql() -> str:
    """Таблица товаров (вкусов)"""
    return """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL,
        flavor TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
        UNIQUE(brand_id, flavor)
    );
    """


def create_sales_table_sql() -> str:
    return """
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """


# ===== BRANDS =====

def insert_brand_sql() -> str:
    return """
    INSERT INTO brands (name, category)
    VALUES (:name, :category);
    """


def select_brand_by_name_and_category_sql() -> str:
    return """
    SELECT id, name, category
    FROM brands
    WHERE name = :name AND category = :category
    LIMIT 1;
    """


def select_brands_by_category_sql() -> str:
    return """
    SELECT id, name, category
    FROM brands
    WHERE category = :category
    ORDER BY name;
    """


def select_all_brands_sql() -> str:
    return """
    SELECT id, name, category
    FROM brands
    ORDER BY category, name;
    """


# ===== PRODUCTS =====

def insert_product_sql() -> str:
    return """
    INSERT INTO products (brand_id, flavor, quantity, price)
    VALUES (:brand_id, :flavor, :quantity, :price);
    """


def select_product_by_brand_and_flavor_sql() -> str:
    return """
    SELECT 
        p.id,
        p.brand_id,
        b.name as brand_name,
        b.category,
        p.flavor,
        p.quantity,
        p.price
    FROM products p
    JOIN brands b ON p.brand_id = b.id
    WHERE p.brand_id = :brand_id AND p.flavor = :flavor
    LIMIT 1;
    """


def select_products_by_brand_sql() -> str:
    return """
    SELECT 
        p.id,
        p.brand_id,
        b.name as brand_name,
        b.category,
        p.flavor,
        p.quantity,
        p.price
    FROM products p
    JOIN brands b ON p.brand_id = b.id
    WHERE p.brand_id = :brand_id
    ORDER BY p.flavor;
    """


def select_all_products_sql() -> str:
    return """
    SELECT 
        p.id,
        p.brand_id,
        b.name as brand_name,
        b.category,
        p.flavor,
        p.quantity,
        p.price
    FROM products p
    JOIN brands b ON p.brand_id = b.id
    ORDER BY b.category, b.name, p.flavor;
    """


def select_products_by_category_sql() -> str:
    return """
    SELECT 
        p.id,
        p.brand_id,
        b.name as brand_name,
        b.category,
        p.flavor,
        p.quantity,
        p.price
    FROM products p
    JOIN brands b ON p.brand_id = b.id
    WHERE b.category = :category
    ORDER BY b.name, p.flavor;
    """


def update_product_quantity_sql() -> str:
    return """
    UPDATE products
    SET quantity = :quantity
    WHERE id = :id;
    """


def delete_product_sql() -> str:
    return """
    DELETE FROM products
    WHERE id = :id;
    """

def select_brand_by_id_sql() -> str:
    return """
    SELECT id, name, category
    FROM brands
    WHERE id = :id
    """

# ===== SALES =====

def insert_sale_sql() -> str:
    return """
    INSERT INTO sales (product_id, admin_id, quantity, price, sale_date)
    VALUES (:product_id, :admin_id, :quantity, :price, :sale_date);
    """


def select_all_sales_sql() -> str:
    return """
    SELECT 
        s.id,
        s.product_id,
        p.flavor as product_flavor,
        b.name as brand_name,
        b.category,
        s.admin_id,
        s.quantity,
        s.price,
        s.sale_date
    FROM sales s
    JOIN products p ON s.product_id = p.id
    JOIN brands b ON p.brand_id = b.id
    ORDER BY s.sale_date DESC;
    """


def select_sales_by_date_range_sql() -> str:
    return """
    SELECT 
        s.id,
        s.product_id,
        p.flavor as product_flavor,
        b.name as brand_name,
        b.category,
        s.admin_id,
        s.quantity,
        s.price,
        s.sale_date
    FROM sales s
    JOIN products p ON s.product_id = p.id
    JOIN brands b ON p.brand_id = b.id
    WHERE s.sale_date BETWEEN :start_date AND :end_date
    ORDER BY s.sale_date DESC;
    """