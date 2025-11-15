-- 1. CLEAN SLATE: Reset the entire database
DROP DATABASE IF EXISTS Meal_Manufacturer;
CREATE DATABASE Meal_Manufacturer;
USE Meal_Manufacturer;

-- 2. BUILD TABLES: Run your schema file first
SOURCE sql_src/schema.sql;   

-- 3. BUILD LOGIC: NOW run your procedures/triggers file
SOURCE sql_src/procedures_triggers.sql;   

-- -- 4. POPULATE DATA: Now that tables and logic exist, add data
SOURCE sql_src/data.sql;
-- =====================================================================
-- TEST FOR: trg_compute_ingredient_lot_number
-- =====================================================================

-- We'll print this to the console so we know which test is running.
SELECT 'TESTING: Trigger for IngredientBatch lot number creation' AS test_name;

-- ---------------------------------------------------------------------
-- Test 1: (Happy Path) Check if the lot_number is built correctly.
-- ---------------------------------------------------------------------

-- ACTION:
-- Insert a new ingredient batch using *REAL* data from populate.sql
-- We'll use Ingredient '101' (Salt) and Supplier '20' (Jane Doe)
INSERT INTO IngredientBatch 
  (ingredient_id, supplier_id, supplier_batch_id, 
   quantity_on_hand, per_unit_cost, expiration_date, intake_date)
VALUES 
  ('101', '20', 'B-12345-TEST', 
   100.00, 5.50, '2026-11-15', '2025-11-15');

-- CHECK:
-- Select the row we just inserted (using the unique 'supplier_batch_id')
-- and check what the database automatically set as the 'lot_number'.
SELECT lot_number 
FROM IngredientBatch 
WHERE supplier_batch_id = 'B-12345-TEST';

-- EXPECTED OUTPUT FOR TEST 1:
-- +-----------------------------+
-- | lot_number                  |
-- +-----------------------------+
-- | 101-20-B-12345-TEST         |
-- +-----------------------------+


-- ---------------------------------------------------------------------
-- Test 2: (Uniqueness) Check if the PRIMARY KEY blocks a duplicate.
-- ---------------------------------------------------------------------

SELECT 'TESTING: Uniqueness constraint for lot_number' AS test_name;

-- ACTION:
-- Try to insert the *exact same* combination.
-- The trigger will try to build the *same* lot_number ('101-20-B-12345-TEST').
-- The database's PRIMARY KEY constraint should reject this INSERT.
INSERT INTO IngredientBatch 
  (ingredient_id, supplier_id, supplier_batch_id, 
   quantity_on_hand, per_unit_cost, expiration_date, intake_date)
VALUES 
  ('101', '20', 'B-12345-TEST', 
   50.00, 5.25, '2026-11-20', '2025-11-20');

-- CHECK:
-- This test PASSES if this command prints a "Duplicate entry" ERROR.
-- If this INSERT *succeeds*, your test has FAILED.

-- EXPECTED OUTPUT FOR TEST 2:
-- ERROR 1062 (23000): Duplicate entry '101-20-B-12345-TEST' for key 'IngredientBatch.PRIMARY'