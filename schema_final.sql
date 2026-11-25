-- Suppression des tables existantes (tables avec clés étrangères d'abord)
DROP TABLE IF EXISTS sales_by_country;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS countries;
DROP TABLE IF EXISTS channels;

-- Dimensions
CREATE TABLE books (
    book_id TEXT PRIMARY KEY NOT NULL,
    book_name TEXT,
    price_gbp REAL
);

CREATE TABLE countries (
    country_code TEXT PRIMARY KEY NOT NULL,
    country_name TEXT,
    currency_code TEXT,
    vat_rate REAL,
    region TEXT,
    is_active INTEGER
);

CREATE TABLE channels (
    channel_code TEXT PRIMARY KEY NOT NULL,
    channel_name TEXT,
    acquisition_cost_gbp REAL,
    channel_group TEXT,
    is_active INTEGER
);

-- Faits
CREATE TABLE sales (
    order_id TEXT PRIMARY KEY NOT NULL,
    order_date TEXT,
    book_id TEXT,
    country_code TEXT,
    channel_code TEXT,
    quantity INTEGER,
    discount_rate REAL,
    price_gbp REAL,
    taux_gbp_eur REAL,
    revenue_gbp REAL,
    revenue_eur REAL,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (country_code) REFERENCES countries(country_code),
    FOREIGN KEY (channel_code) REFERENCES channels(channel_code)
);

-- Agrégat
CREATE TABLE sales_by_country (
    country_code TEXT PRIMARY KEY NOT NULL,
    country_name TEXT,
    total_orders INTEGER,
    total_quantity INTEGER,
    total_revenue_gbp REAL,
    total_revenue_eur REAL
);