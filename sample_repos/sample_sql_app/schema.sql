-- Sample database schema for e-commerce application

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    loyalty_points INTEGER DEFAULT 0,
    CONSTRAINT email_format CHECK (email LIKE '%@%.%'),
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'suspended')),
    CONSTRAINT positive_points CHECK (loyalty_points >= 0)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_price CHECK (price > 0),
    CONSTRAINT non_negative_stock CHECK (stock_quantity >= 0)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL,
    discount_amount NUMERIC(10, 2) DEFAULT 0,
    final_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    CONSTRAINT positive_total CHECK (total_amount >= 0),
    CONSTRAINT valid_discount CHECK (discount_amount >= 0 AND discount_amount <= total_amount),
    CONSTRAINT valid_order_status CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    line_total NUMERIC(10, 2) NOT NULL,
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_unit_price CHECK (unit_price >= 0)
);

CREATE INDEX idx_customer_email ON customers(email);
CREATE INDEX idx_order_customer ON orders(customer_id);
CREATE INDEX idx_order_date ON orders(order_date);
CREATE INDEX idx_product_category ON products(category);
