def create_products_table_sql() -> str:
    return """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


def insert_product_sql() -> str:
    return """
    INSERT INTO products (title, category, quantity, price)
    VALUES (:title, :category, :quantity, :price);
    """


def insert_sale_sql() -> str:
    return """
    INSERT INTO sales (product_id, admin_id, quantity, price, sale_date)
    VALUES (:product_id, :admin_id, :quantity, :price, :sale_date);
    """


def select_all_products_sql() -> str:
    return """
    SELECT id, title, category, quantity, price
    FROM products
    ORDER BY category, title;
    """


def select_products_by_category_sql() -> str:
    return """
    SELECT id, title, category, quantity, price
    FROM products
    WHERE category = :category
    ORDER BY title;
    """


def select_product_by_title_and_category_sql() -> str:
    return """
    SELECT id, title, category, quantity, price
    FROM products
    WHERE title = :title AND category = :category
    LIMIT 1;
    """


def select_all_sales_sql() -> str:
    return """
    SELECT 
        s.id,
        s.product_id,
        p.title as product_title,
        p.category as product_category,
        s.admin_id,
        s.quantity,
        s.price,
        s.sale_date
    FROM sales s
    JOIN products p ON s.product_id = p.id
    ORDER BY s.sale_date DESC;
    """


def select_sales_by_date_range_sql() -> str:
    return """
    SELECT 
        s.id,
        s.product_id,
        p.title as product_title,
        p.category as product_category,
        s.admin_id,
        s.quantity,
        s.price,
        s.sale_date
    FROM sales s
    JOIN products p ON s.product_id = p.id
    WHERE s.sale_date BETWEEN :start_date AND :end_date
    ORDER BY s.sale_date DESC;
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