# Error Explanation and Solution

## What Went Wrong?

The errors you encountered are due to the Python setup script trying to parse MySQL SQL files by splitting them by semicolons (`;`). However, MySQL has special syntax for triggers and stored procedures that uses `DELIMITER` statements, which the simple parsing approach cannot handle.

### Root Causes:

1. **DELIMITER Statements**: 
   - MySQL uses `DELIMITER //` to change the statement delimiter when defining triggers/procedures
   - The Python script splits by `;`, breaking trigger/procedure definitions
   - Example: A trigger definition spans multiple lines between `DELIMITER //` and `DELIMITER ;`

2. **Multi-line Statements**:
   - Triggers and stored procedures contain control flow (IF/END IF, LOOP/END LOOP)
   - These cannot be split by semicolons
   - The script tried to execute incomplete statements

3. **Inline Comments**:
   - `data.sql` has inline comments like `-- 8 oz Beef Steak`
   - The script didn't properly strip these, causing syntax errors

4. **Cascading Failures**:
   - When triggers/procedures failed, tables that reference them also failed
   - Example: `INGREDIENT_BATCHES` table creation failed because trigger creation failed first

## Error Breakdown

### Error Type 1: Syntax Errors
```
Error in statement 7: 1064 (42000): You have an error in your SQL syntax
Statement: CREATE TABLE INGREDIENT_COMPOSITIONS ( parent_ingredient_id INT NOT NULL...
```
**Cause**: The script split a multi-line CREATE TABLE statement incorrectly, or comments weren't stripped properly.

### Error Type 2: Missing Tables
```
Error: 1824 (HY000): Failed to open the referenced table 'formulation_versions'
Error: 1146 (42S02): Table 'csc_540.ingredient_batches' doesn't exist
```
**Cause**: Earlier table creation failed, so dependent tables can't be created.

### Error Type 3: Trigger/Procedure Errors
```
Error: 1064 (42000): You have an error in your SQL syntax near 'DELIMITER //'
Error: 1327 (42000): Undeclared variable: batch_counter
```
**Cause**: The script tried to execute trigger/procedure code as separate statements, breaking the logic.

### Error Type 4: Foreign Key Constraint Failures
```
Error: 1452 (23000): Cannot add or update a child row: a foreign key constraint fails
```
**Cause**: Tables weren't created properly, so foreign key relationships don't exist.

## The Solution

**Use MySQL command line directly** - It handles all MySQL-specific syntax correctly.

### Why MySQL Command Line Works:

1. **Native MySQL Parser**: Understands `DELIMITER` statements
2. **No Parsing Issues**: Executes SQL exactly as written
3. **Handles All Features**: Triggers, procedures, views, etc.
4. **Reliable**: Same method used by database administrators worldwide

## How to Fix It

### Method 1: Use MySQL Command Line (Recommended)

```bash
# 1. Create database
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS csc_540;"

# 2. Load schema (this will work correctly with DELIMITER)
mysql -u root -p csc_540 < schema.sql

# 3. Load data
mysql -u root -p csc_540 < data.sql
```

### Method 2: Use MySQL Workbench

1. Open MySQL Workbench
2. Connect to your database
3. Open `schema.sql` and execute it (File → Open SQL Script)
4. Open `data.sql` and execute it

### Method 3: Use the Batch File (Windows)

1. Double-click `setup.bat`
2. Enter your MySQL password when prompted
3. Wait for completion

## Verification

After running the setup correctly, verify with:

```sql
USE csc_540;

-- Check tables (should show 16 tables)
SHOW TABLES;

-- Check triggers (should show 5 triggers)
SHOW TRIGGERS;

-- Check procedures (should show 3 procedures)
SHOW PROCEDURE STATUS WHERE Db = 'csc_540';

-- Check views (should show 3 views)
SHOW FULL TABLES WHERE Table_type = 'VIEW';

-- Check data
SELECT COUNT(*) FROM USERS;  -- Should show 8
SELECT COUNT(*) FROM PRODUCTS;  -- Should show multiple products
```

## Expected Results After Fix

✅ **16 tables** created successfully
✅ **5 triggers** created successfully  
✅ **3 stored procedures** created successfully
✅ **3 views** created successfully
✅ **Sample data** loaded (users, products, batches, etc.)

## Why Python Script Failed

The Python script used this approach:
```python
statements = sql_script.split(';')
for statement in statements:
    cursor.execute(statement)
```

This works for simple SQL but fails for:
- `DELIMITER // ... DELIMITER ;` blocks
- Multi-line trigger/procedure definitions
- Complex control flow in stored procedures

## Updated Python Script

The updated `setup_database.py` now:
1. **Tries to use MySQL command line first** (if available)
2. **Falls back to Python connector** with better error handling
3. **Provides clear instructions** if it can't handle DELIMITER

However, **MySQL command line is still recommended** for reliability.

## Quick Fix Summary

**Just run these three commands:**

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS csc_540;"
mysql -u root -p csc_540 < schema.sql
mysql -u root -p csc_540 < data.sql
```

That's it! This will work correctly and handle all MySQL-specific syntax.

## Still Having Issues?

1. **Check MySQL is running**: `mysql -u root -p` should connect
2. **Check database name**: Make sure it's `csc_540` (or update SQL files)
3. **Check file paths**: Make sure `schema.sql` and `data.sql` are in the current directory
4. **Check permissions**: Make sure MySQL user has CREATE privileges
5. **Check MySQL version**: Should be MySQL 5.7+ or MariaDB 10.2+

## Alternative: Manual Setup in MySQL Workbench

If command line doesn't work:

1. Open MySQL Workbench
2. Connect to your server
3. Create database: `CREATE DATABASE csc_540;`
4. Select database: `USE csc_540;`
5. Open `schema.sql` in Workbench
6. Execute it (⚡ button)
7. Open `data.sql` in Workbench  
8. Execute it (⚡ button)

Workbench handles DELIMITER statements correctly.

