# Database Setup Instructions

## Overview of SQL Files

### 1. `schema.sql`
**Purpose**: Creates the database structure
- Creates all tables (USERS, PRODUCTS, INGREDIENTS, etc.)
- Defines all constraints (primary keys, foreign keys, unique constraints)
- Creates triggers (lot number computation, expiration checks, inventory updates)
- Creates stored procedures (batch creation, recall traceability, health risk evaluation)
- Creates views (active formulations, flattened BOM, health risk violations)
- Sets up indexes for performance

**When to use**: Run this FIRST to create the database structure. This must be run before `data.sql`.

### 2. `data.sql`
**Purpose**: Populates the database with sample data
- Inserts sample users (manufacturers, suppliers, viewers)
- Inserts sample products, ingredients, categories
- Inserts sample batches and consumption records
- Inserts sample recipe plans
- Inserts do-not-combine rules

**When to use**: Run this SECOND, after `schema.sql`. This loads sample data for testing.

### 3. `queries.sql`
**Purpose**: Contains the 5 required queries for the project
- Query 1: Ingredients and lot numbers of last Steak Dinner batch by MFG001
- Query 2: Suppliers and total spending for MFG002
- Query 3: Unit cost for product lot 100-MFG001-B0901
- Query 4: Conflicting ingredients for product lot 100-MFG001-B0901
- Query 5: Manufacturers NOT supplied by James Miller (21)

**When to use**: 
- Reference for the required queries
- Can be run individually to test queries
- Also accessible through the application's "View Queries" menu

## Setup Methods

### Method 1: Using the Python Setup Script (Recommended)

1. **Update database credentials** in `setup_database.py`:
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'port': 3306,
       'user': 'root',
       'password': 'YOUR_PASSWORD',  # Update this
       'database': 'csc_540'  # Update if different
   }
   ```

2. **Run the setup script**:
   ```bash
   python setup_database.py
   ```

This script will:
- Create the database if it doesn't exist
- Load the schema (tables, triggers, procedures, views)
- Load sample data
- Verify the installation

### Method 2: Using MySQL Command Line

1. **Open MySQL command line**:
   ```bash
   mysql -u root -p
   ```

2. **Create database** (if not exists):
   ```sql
   CREATE DATABASE IF NOT EXISTS csc_540;
   USE csc_540;
   ```

3. **Load schema**:
   ```bash
   mysql -u root -p csc_540 < schema.sql
   ```
   Or in MySQL prompt:
   ```sql
   SOURCE schema.sql;
   ```

4. **Load data**:
   ```bash
   mysql -u root -p csc_540 < data.sql
   ```
   Or in MySQL prompt:
   ```sql
   SOURCE data.sql;
   ```

### Method 3: Using MySQL Workbench

1. **Open MySQL Workbench** and connect to your database

2. **Open `schema.sql`**:
   - File → Open SQL Script → Select `schema.sql`
   - Click the "Execute" button (⚡) or press Ctrl+Shift+Enter
   - Wait for completion

3. **Open `data.sql`**:
   - File → Open SQL Script → Select `data.sql`
   - Click the "Execute" button (⚡) or press Ctrl+Shift+Enter
   - Wait for completion

4. **Verify**: Check that tables are created and data is loaded

### Method 4: Using phpMyAdmin or Other GUI Tools

1. **Select your database** (`csc_540`)

2. **Import `schema.sql`**:
   - Go to Import tab
   - Choose file: `schema.sql`
   - Click Go

3. **Import `data.sql`**:
   - Go to Import tab
   - Choose file: `data.sql`
   - Click Go

## Verification

After setup, verify the installation:

```sql
-- Check tables
SHOW TABLES;

-- Check users
SELECT COUNT(*) FROM USERS;

-- Check products
SELECT COUNT(*) FROM PRODUCTS;

-- Check ingredient batches
SELECT COUNT(*) FROM INGREDIENT_BATCHES;

-- Check product batches
SELECT COUNT(*) FROM PRODUCT_BATCHES;
```

## Running Queries

### Option 1: Through the Application
1. Run the application: `python src/inventory_app.py`
2. Select "4. View Queries" from the main menu
3. Choose which query to run

### Option 2: Directly in MySQL
1. Open MySQL command line or Workbench
2. Use database: `USE csc_540;`
3. Copy and paste individual queries from `queries.sql`
4. Execute each query

### Option 3: Run All Queries from File
```bash
mysql -u root -p csc_540 < queries.sql
```

## Troubleshooting

### Error: "Access denied for user 'root'@'localhost'"
- Check your MySQL password
- Update password in `setup_database.py` or use `-p` flag in command line

### Error: "Unknown database 'csc_540'"
- Create the database first: `CREATE DATABASE csc_540;`
- Or update database name in SQL files to match your database

### Error: "Table already exists"
- Drop and recreate: `DROP DATABASE csc_540; CREATE DATABASE csc_540;`
- Or use: `DROP TABLE IF EXISTS table_name;` before creating

### Error: "Foreign key constraint fails"
- Make sure `schema.sql` runs completely before `data.sql`
- Check that data insertion order matches table dependencies

### Error: "Duplicate entry"
- The database already has data
- Drop and recreate the database, or delete existing data first

## Sample Login Credentials

After loading `data.sql`, you can login with:

**Manufacturers:**
- Username: `mfg001_user`, Password: `password123`
- Username: `mfg002_user`, Password: `password123`
- Username: `mfg003_user`, Password: `password123`

**Suppliers:**
- Username: `supplier21_user`, Password: `password123` (James Miller)
- Username: `supplier22_user`, Password: `password123` (Sarah Williams)
- Username: `supplier23_user`, Password: `password123` (Mike Brown)

**Viewers:**
- Username: `viewer1`, Password: `password123`
- Username: `viewer2`, Password: `password123`

## Important Notes

1. **Order matters**: Always run `schema.sql` before `data.sql`
2. **Database name**: All SQL files use `csc_540`. Update if your database has a different name.
3. **Passwords**: Update database passwords in `setup_database.py` and `inventory_app.py`
4. **Data persistence**: Data persists between application runs. To reset, drop and recreate the database.

