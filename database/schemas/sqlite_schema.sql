-- DupeFinder Database Schema (PostgreSQL)
-- Professional relational database for product catalog

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    image_path VARCHAR(500) NOT NULL,
    embedding_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);

-- Search history table (optional, for analytics)
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    query_image_path VARCHAR(500),
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_results INTEGER,
    top_result_id INTEGER,
    FOREIGN KEY (top_result_id) REFERENCES products(id) ON DELETE SET NULL
);

-- Create index for search history
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(search_timestamp);

-- Add comments
COMMENT ON TABLE products IS 'Fashion product catalog with metadata';
COMMENT ON TABLE search_history IS 'User search query history for analytics';

