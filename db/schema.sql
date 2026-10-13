-- «Чудо Обувь» / PostgreSQL 12+. ВНИМАНИЕ: повторный запуск удаляет данные.
BEGIN;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS stock_items CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS sizes CASCADE;
DROP TABLE IF EXISTS manufacturers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(70) NOT NULL UNIQUE
);
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    login VARCHAR(100) NOT NULL UNIQUE,
    role_id INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT
);
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(150) NOT NULL UNIQUE
);
CREATE TABLE manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    manufacturer_name VARCHAR(200) NOT NULL UNIQUE
);
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(manufacturer_id),
    subcategory VARCHAR(150),
    product_name VARCHAR(255) NOT NULL,
    image_path VARCHAR(255),
    description TEXT,
    composition TEXT,
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    UNIQUE (product_name, manufacturer_id)
);
CREATE TABLE sizes (
    size_id SERIAL PRIMARY KEY,
    size_value NUMERIC(4,1) NOT NULL UNIQUE CHECK (size_value > 0)
);
CREATE TABLE stock_items (
    stock_item_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    size_id INTEGER NOT NULL REFERENCES sizes(size_id) ON DELETE RESTRICT,
    quantity_available INTEGER NOT NULL DEFAULT 0 CHECK (quantity_available >= 0),
    UNIQUE (product_id, size_id)
);
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT
);
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    stock_item_id INTEGER NOT NULL REFERENCES stock_items(stock_item_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0)
);
CREATE INDEX idx_stock_product ON stock_items(product_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_stock ON order_items(stock_item_id);
COMMIT;
