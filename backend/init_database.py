"""
DupeFinder Backend - Database Initialization
Task 3.1 & 3.2: Initialize PostgreSQL database and populate with products

This script:
- Connects to PostgreSQL
- Creates tables from schema
- Imports products from CSV
- Verifies database setup
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from pathlib import Path
import sys
import os

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'database': os.getenv('DB_NAME', 'dupefinder')
}

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (default postgres database)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['database']}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"[OK] Database '{DB_CONFIG['database']}' created")
        else:
            print(f"[OK] Database '{DB_CONFIG['database']}' already exists")
        
        cursor.close()
        conn.close()
        
        return True
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to create database: {e}")
        return False

def create_tables():
    """Connect to database and create tables"""
    print("=" * 60)
    print("STEP 1: Creating Database Tables")
    print("=" * 60)
    
    # Create database if needed
    if not create_database_if_not_exists():
        return None
    
    # Read schema
    schema_path = Path("database/schemas/postgresql_schema.sql")
    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}")
        return None
    
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    try:
        # Connect to our database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Execute schema
        cursor.execute(schema)
        conn.commit()
        
        print(f"[OK] Connected to PostgreSQL")
        print(f"[OK] Database: {DB_CONFIG['database']}")
        print(f"[OK] Tables created successfully")
        
        return conn
    except psycopg2.Error as e:
        print(f"[ERROR] Database error: {e}")
        return None

def import_products(conn):
    """Import products from CSV"""
    print("\n" + "=" * 60)
    print("STEP 2: Importing Products")
    print("=" * 60)
    
    catalog_path = Path("data/product_catalog.csv")
    
    if not catalog_path.exists():
        print(f"[ERROR] Product catalog not found: {catalog_path}")
        return False
    
    # Load CSV
    catalog = pd.read_csv(catalog_path)
    print(f"[OK] Loaded {len(catalog)} products from CSV")
    
    # Fix image paths
    catalog['image_path'] = catalog['image_path'].str.replace('\\\\', '/')
    
    # Prepare embedding paths
    catalog['embedding_path'] = 'data/embeddings/product_embeddings.pkl'
    
    # Insert into database
    cursor = conn.cursor()
    
    for idx, row in catalog.iterrows():
        cursor.execute("""
            INSERT INTO products (name, category, brand, price, description, image_path, embedding_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['name'],
            row['category'],
            row['brand'],
            float(row['price']),
            row['description'],
            row['image_path'],
            catalog['embedding_path'].iloc[0]
        ))
    
    conn.commit()
    
    print(f"[OK] Imported {len(catalog)} products into database")
    
    return True

def verify_database(conn):
    """Verify database contents"""
    print("\n" + "=" * 60)
    print("STEP 3: Verifying Database")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Count products
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"[OK] Total products in database: {count}")
    
    # Count by category
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM products 
        GROUP BY category 
        ORDER BY category
    """)
    
    print(f"\n     Products by category:")
    for category, cat_count in cursor.fetchall():
        print(f"       - {category}: {cat_count}")
    
    # Sample products
    cursor.execute("SELECT id, name, category, brand, price FROM products LIMIT 5")
    print(f"\n     Sample products:")
    for prod in cursor.fetchall():
        print(f"       {prod[0]}. {prod[1]} ({prod[2]}) - {prod[3]} - ${prod[4]}")
    
    print("\n[SUCCESS] Database verification complete!")
    
    return True

def main():
    """Main initialization workflow"""
    print("\n" + "=" * 60)
    print("DupeFinder Backend - Database Initialization")
    print("Tasks 3.1 & 3.2: PostgreSQL Setup")
    print("=" * 60 + "\n")
    
    print(f"[INFO] Connecting to PostgreSQL...")
    print(f"       Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"       Database: {DB_CONFIG['database']}")
    print(f"       User: {DB_CONFIG['user']}")
    print()
    
    # Create tables
    conn = create_tables()
    if conn is None:
        print("\n[FAILED] Database initialization failed!")
        print("\n[TIP] Make sure PostgreSQL is installed and running:")
        print("      1. Install PostgreSQL: https://www.postgresql.org/download/")
        print("      2. Start PostgreSQL service")
        print("      3. Update DB credentials in environment variables or defaults")
        return 1
    
    # Import products
    if not import_products(conn):
        conn.close()
        return 1
    
    # Verify
    if not verify_database(conn):
        conn.close()
        return 1
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    print("[COMPLETE] Database initialization complete!")
    print("=" * 60)
    print(f"\nPostgreSQL database ready: {DB_CONFIG['database']}")
    print("You can now start the FastAPI backend!")
    print("\nNext: python backend/main.py\n")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

