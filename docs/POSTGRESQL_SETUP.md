# PostgreSQL Setup Guide for DupeFinder

## Overview

DupeFinder uses PostgreSQL as the primary database for storing product catalog and metadata.

**Database**: `dupefinder`  
**Default Credentials**: `postgres` / `postgres`  
**Port**: `5432`

---

## Installation Instructions

### Option 1: Install PostgreSQL (Windows)

**Step 1: Download PostgreSQL**
- Go to: https://www.postgresql.org/download/windows/
- Download the installer (PostgreSQL 15 or higher recommended)
- File size: ~200 MB

**Step 2: Run Installer**
- Run the downloaded .exe file
- Click "Next" through the wizard
- Select components: Install all (PostgreSQL Server, pgAdmin, Command Line Tools)
- Choose installation directory (default is fine)
- **Important**: Set superuser password (remember this!) - use `postgres` for simplicity
- Port: `5432` (default)
- Locale: Default locale
- Complete installation

**Step 3: Verify Installation**
```powershell
# Check if PostgreSQL is running
Get-Service -Name postgresql*

# Should show "Running" status
```

**Step 4: Test Connection**
```powershell
# Connect to PostgreSQL
psql -U postgres

# If prompted for password, enter the password you set during installation
# You should see: postgres=#
# Type \q to quit
```

---

### Option 2: Use Docker (Alternative)

If you prefer Docker (easier, no system installation):

```powershell
# Pull PostgreSQL image
docker pull postgres:15

# Run PostgreSQL container
docker run --name dupefinder-postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=dupefinder `
  -p 5432:5432 `
  -d postgres:15

# Verify it's running
docker ps

# To stop: docker stop dupefinder-postgres
# To start: docker start dupefinder-postgres
```

---

## Configuration

### Default Configuration (Already Set)

The database initialization script uses these defaults:

```python
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_NAME = 'dupefinder'
```

### Custom Configuration (Optional)

If you want different credentials, set environment variables:

**Windows PowerShell:**
```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_USER = "your_username"
$env:DB_PASSWORD = "your_password"
$env:DB_NAME = "dupefinder"
```

**Or create `.env` file:**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=dupefinder
```

---

## Initialize Database

Once PostgreSQL is installed and running:

```powershell
# Navigate to project directory
cd C:\Users\ab887\Desktop\dupefinder

# Install backend dependencies (if not done)
pip install psycopg2-binary pandas

# Run database initialization
python backend/init_database.py
```

**Expected Output:**
```
============================================================
DupeFinder Backend - Database Initialization
Tasks 3.1 & 3.2: PostgreSQL Setup
============================================================

[INFO] Connecting to PostgreSQL...
       Host: localhost:5432
       Database: dupefinder
       User: postgres

============================================================
STEP 1: Creating Database Tables
============================================================
[OK] Database 'dupefinder' created
[OK] Connected to PostgreSQL
[OK] Database: dupefinder
[OK] Tables created successfully

============================================================
STEP 2: Importing Products
============================================================
[OK] Loaded 100 products from CSV
[OK] Imported 100 products into database

============================================================
STEP 3: Verifying Database
============================================================
[OK] Total products in database: 100

     Products by category:
       - accessories: 20
       - bags: 20
       - clothing: 20
       - shoes: 20
       - watches: 20

[COMPLETE] Database initialization complete!
```

---

## Verify Database

### Using psql (Command Line)

```powershell
# Connect to database
psql -U postgres -d dupefinder

# List tables
\dt

# Count products
SELECT COUNT(*) FROM products;

# View sample products
SELECT id, name, category, brand, price FROM products LIMIT 5;

# Exit
\q
```

### Using pgAdmin (GUI)

1. Open pgAdmin (installed with PostgreSQL)
2. Connect to server (localhost)
3. Navigate to: Servers → PostgreSQL → Databases → dupefinder
4. Right-click → Query Tool
5. Run queries to explore data

---

## Troubleshooting

### Issue: "psql: command not found"

**Solution**: Add PostgreSQL to PATH

1. Find PostgreSQL installation directory (usually `C:\Program Files\PostgreSQL\15\bin`)
2. Add to System PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Program Files\PostgreSQL\15\bin`
   - Restart terminal

### Issue: "connection refused"

**Solution**: Start PostgreSQL service

```powershell
# Check service status
Get-Service -Name postgresql*

# Start service
Start-Service postgresql-x64-15

# Or use Services app (services.msc)
```

### Issue: "password authentication failed"

**Solution**: Reset password or use correct credentials

```powershell
# Connect as postgres user
psql -U postgres

# Change password
ALTER USER postgres PASSWORD 'postgres';
```

### Issue: "database dupefinder does not exist"

**Solution**: The init script creates it automatically. If manual creation needed:

```sql
CREATE DATABASE dupefinder;
```

---

## What's Next?

After successful database initialization:

1. ✅ PostgreSQL installed and running
2. ✅ Database `dupefinder` created
3. ✅ Tables `products` and `search_history` created
4. ✅ 100 products imported

**Next Step**: Build FastAPI backend (Task 3.4)
```powershell
python backend/main.py
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start PostgreSQL | `Start-Service postgresql-x64-15` |
| Stop PostgreSQL | `Stop-Service postgresql-x64-15` |
| Connect to DB | `psql -U postgres -d dupefinder` |
| List databases | `\l` (in psql) |
| List tables | `\dt` (in psql) |
| View products | `SELECT * FROM products;` |
| Count products | `SELECT COUNT(*) FROM products;` |

---

## Database Schema

```sql
-- Products Table
CREATE TABLE products (
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

-- Search History Table
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    query_image_path VARCHAR(500),
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_results INTEGER,
    top_result_id INTEGER,
    FOREIGN KEY (top_result_id) REFERENCES products(id)
);
```

---

## Support

If you encounter issues:
1. Check PostgreSQL is running: `Get-Service -Name postgresql*`
2. Verify connection: `psql -U postgres`
3. Check logs: `C:\Program Files\PostgreSQL\15\data\log\`
4. Refer to official docs: https://www.postgresql.org/docs/










