-- DupeFinder Database Schema (PostgreSQL)
-- Professional relational database for product catalog

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS search_history CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    description TEXT,
    image_path VARCHAR(500) NOT NULL,
    embedding_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_created_at ON products(created_at DESC);

-- Search history table (for analytics - 40% milestone)
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    query_image_path VARCHAR(500),
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_results INTEGER,
    top_result_id INTEGER,
    FOREIGN KEY (top_result_id) REFERENCES products(id) ON DELETE SET NULL
);

-- Create index for search history
CREATE INDEX idx_search_history_timestamp ON search_history(search_timestamp DESC);

-- Add table comments
COMMENT ON TABLE products IS 'Fashion product catalog with metadata and embeddings';
COMMENT ON TABLE search_history IS 'User search query history for analytics';

-- Add column comments
COMMENT ON COLUMN products.id IS 'Unique product identifier';
COMMENT ON COLUMN products.name IS 'Product name/title';
COMMENT ON COLUMN products.category IS 'Product category (bags, shoes, watches, clothing, accessories)';
COMMENT ON COLUMN products.brand IS 'Brand/manufacturer name';
COMMENT ON COLUMN products.price IS 'Product price in USD';
COMMENT ON COLUMN products.image_path IS 'Relative path to product image';
COMMENT ON COLUMN products.embedding_path IS 'Path to pre-computed embedding file';
