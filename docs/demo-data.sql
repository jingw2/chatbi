-- ChatBI demo dataset for PostgreSQL.
-- Usage:
--   createdb chatbi_demo
--   psql -d chatbi_demo -f docs/demo-data.sql
--
-- Then add a ChatBI datasource pointing at this database with a read-only user.

DROP SCHEMA IF EXISTS chatbi_demo CASCADE;
CREATE SCHEMA chatbi_demo;
SET search_path TO chatbi_demo;

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    region TEXT NOT NULL,
    city TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_no TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date DATE NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    payment_method TEXT NOT NULL
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    gross_amount NUMERIC(12, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    net_amount NUMERIC(12, 2) GENERATED ALWAYS AS (quantity * unit_price - discount_amount) STORED
);

CREATE TABLE inventory_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(id),
    warehouse_region TEXT NOT NULL,
    on_hand_qty INTEGER NOT NULL,
    reserved_qty INTEGER NOT NULL
);

CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    ship_date DATE NOT NULL,
    delivery_date DATE,
    carrier TEXT NOT NULL,
    shipping_region TEXT NOT NULL,
    shipping_cost NUMERIC(12, 2) NOT NULL
);

CREATE TABLE returns (
    id SERIAL PRIMARY KEY,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id),
    return_date DATE NOT NULL,
    reason TEXT NOT NULL,
    returned_qty INTEGER NOT NULL
);

INSERT INTO customers (customer_name, segment, region, city, signup_date) VALUES
('Acme Retail', 'Enterprise', 'East', 'Shanghai', '2023-01-12'),
('Bright Foods', 'SMB', 'East', 'Hangzhou', '2023-03-04'),
('Cedar Logistics', 'Enterprise', 'North', 'Beijing', '2022-11-20'),
('Delta Shop', 'SMB', 'South', 'Guangzhou', '2023-06-18'),
('Evergreen Market', 'Mid-Market', 'South', 'Shenzhen', '2023-02-09'),
('Fortune Store', 'SMB', 'West', 'Chengdu', '2023-07-22'),
('Galaxy Trading', 'Enterprise', 'North', 'Tianjin', '2022-09-15'),
('Harbor Supply', 'Mid-Market', 'East', 'Ningbo', '2023-04-30');

INSERT INTO products (sku, product_name, category, unit_price) VALUES
('SKU-1001', 'Smart Sensor', 'Electronics', 89.00),
('SKU-1002', 'Industrial Router', 'Electronics', 399.00),
('SKU-2001', 'Packing Box L', 'Packaging', 4.50),
('SKU-2002', 'Packing Box M', 'Packaging', 3.20),
('SKU-3001', 'Safety Gloves', 'Supplies', 12.00),
('SKU-3002', 'Barcode Label', 'Supplies', 0.08),
('SKU-4001', 'Thermal Printer', 'Equipment', 249.00),
('SKU-4002', 'Handheld Scanner', 'Equipment', 179.00);

INSERT INTO orders (order_no, customer_id, order_date, channel, status, payment_method) VALUES
('ORD-2024-0001', 1, '2024-01-05', 'Online', 'Delivered', 'Bank Transfer'),
('ORD-2024-0002', 2, '2024-01-11', 'Sales', 'Delivered', 'Credit Card'),
('ORD-2024-0003', 3, '2024-01-18', 'Online', 'Delivered', 'Bank Transfer'),
('ORD-2024-0004', 4, '2024-02-03', 'Marketplace', 'Delivered', 'Credit Card'),
('ORD-2024-0005', 5, '2024-02-14', 'Sales', 'Delivered', 'Bank Transfer'),
('ORD-2024-0006', 6, '2024-02-24', 'Online', 'Cancelled', 'Credit Card'),
('ORD-2024-0007', 7, '2024-03-02', 'Sales', 'Delivered', 'Bank Transfer'),
('ORD-2024-0008', 8, '2024-03-09', 'Online', 'Delivered', 'Credit Card'),
('ORD-2024-0009', 1, '2024-03-17', 'Marketplace', 'Delivered', 'Credit Card'),
('ORD-2024-0010', 4, '2024-03-25', 'Online', 'Delivered', 'Credit Card'),
('ORD-2024-0011', 5, '2024-04-06', 'Sales', 'Delivered', 'Bank Transfer'),
('ORD-2024-0012', 2, '2024-04-18', 'Online', 'Delivered', 'Credit Card');

INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_amount) VALUES
(1, 1, 12, 89.00, 50.00),
(1, 3, 300, 4.50, 0.00),
(2, 2, 3, 399.00, 100.00),
(2, 6, 2000, 0.08, 0.00),
(3, 4, 500, 3.20, 40.00),
(3, 5, 80, 12.00, 0.00),
(4, 8, 8, 179.00, 80.00),
(4, 6, 1500, 0.08, 0.00),
(5, 7, 5, 249.00, 0.00),
(5, 1, 20, 89.00, 120.00),
(6, 2, 2, 399.00, 0.00),
(7, 2, 6, 399.00, 180.00),
(7, 5, 120, 12.00, 50.00),
(8, 3, 800, 4.50, 100.00),
(8, 4, 600, 3.20, 60.00),
(9, 1, 15, 89.00, 0.00),
(9, 8, 10, 179.00, 120.00),
(10, 6, 3000, 0.08, 0.00),
(10, 5, 100, 12.00, 80.00),
(11, 7, 4, 249.00, 50.00),
(11, 8, 6, 179.00, 60.00),
(12, 1, 18, 89.00, 90.00),
(12, 3, 400, 4.50, 0.00);

INSERT INTO inventory_snapshots (snapshot_date, product_id, warehouse_region, on_hand_qty, reserved_qty) VALUES
('2024-04-30', 1, 'East', 260, 45),
('2024-04-30', 1, 'South', 120, 20),
('2024-04-30', 2, 'North', 80, 12),
('2024-04-30', 2, 'East', 55, 8),
('2024-04-30', 3, 'East', 5000, 900),
('2024-04-30', 3, 'South', 3200, 600),
('2024-04-30', 4, 'South', 4100, 700),
('2024-04-30', 5, 'North', 900, 120),
('2024-04-30', 5, 'West', 500, 80),
('2024-04-30', 6, 'East', 40000, 5000),
('2024-04-30', 7, 'South', 70, 10),
('2024-04-30', 8, 'East', 95, 18);

INSERT INTO shipments (order_id, ship_date, delivery_date, carrier, shipping_region, shipping_cost) VALUES
(1, '2024-01-06', '2024-01-08', 'SF Express', 'East', 88.00),
(2, '2024-01-12', '2024-01-15', 'JD Logistics', 'East', 65.00),
(3, '2024-01-19', '2024-01-23', 'DHL', 'North', 120.00),
(4, '2024-02-04', '2024-02-06', 'SF Express', 'South', 72.00),
(5, '2024-02-15', '2024-02-18', 'JD Logistics', 'South', 95.00),
(7, '2024-03-03', '2024-03-07', 'DHL', 'North', 140.00),
(8, '2024-03-10', '2024-03-13', 'SF Express', 'East', 105.00),
(9, '2024-03-18', '2024-03-21', 'JD Logistics', 'East', 98.00),
(10, '2024-03-26', '2024-03-28', 'SF Express', 'South', 56.00),
(11, '2024-04-07', '2024-04-10', 'DHL', 'South', 110.00),
(12, '2024-04-19', '2024-04-22', 'SF Express', 'East', 83.00);

INSERT INTO returns (order_item_id, return_date, reason, returned_qty) VALUES
(7, '2024-02-12', 'Damaged in transit', 1),
(10, '2024-02-26', 'Wrong model', 2),
(17, '2024-03-29', 'Customer changed mind', 1),
(21, '2024-04-16', 'Quality issue', 1);

CREATE VIEW sales_order_summary AS
SELECT
    o.id AS order_id,
    o.order_no,
    o.order_date,
    o.channel,
    o.status,
    c.customer_name,
    c.segment,
    c.region,
    c.city,
    SUM(oi.net_amount) AS net_sales,
    SUM(oi.quantity) AS total_quantity
FROM orders o
JOIN customers c ON c.id = o.customer_id
JOIN order_items oi ON oi.order_id = o.id
GROUP BY
    o.id, o.order_no, o.order_date, o.channel, o.status,
    c.customer_name, c.segment, c.region, c.city;

-- Optional read-only user for ChatBI.
-- Change the password before using outside local demo environments.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'chatbi_demo_readonly') THEN
        CREATE ROLE chatbi_demo_readonly LOGIN PASSWORD 'chatbi_demo_readonly';
    END IF;
END $$;

GRANT USAGE ON SCHEMA chatbi_demo TO chatbi_demo_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA chatbi_demo TO chatbi_demo_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA chatbi_demo GRANT SELECT ON TABLES TO chatbi_demo_readonly;
