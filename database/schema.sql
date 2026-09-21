CREATE TABLE products (product_id TEXT PRIMARY KEY, product_name TEXT, category TEXT, price REAL, cost REAL);
CREATE TABLE customers (customer_id TEXT PRIMARY KEY, customer_name TEXT, city TEXT, orders INTEGER, total_spend REAL, last_order_days INTEGER, segment TEXT);
CREATE TABLE orders (order_id TEXT PRIMARY KEY, customer_id TEXT, product_id TEXT, order_date DATE, quantity INTEGER, revenue REAL, status TEXT);
