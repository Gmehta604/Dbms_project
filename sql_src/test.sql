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

-- SELECT 'TESTING: Uniqueness constraint for lot_number' AS test_name;

-- -- ACTION:
-- -- Try to insert the *exact same* combination.
-- -- The trigger will try to build the *same* lot_number ('101-20-B-12345-TEST').
-- -- The database's PRIMARY KEY constraint should reject this INSERT.
-- INSERT INTO IngredientBatch 
--   (ingredient_id, supplier_id, supplier_batch_id, 
--    quantity_on_hand, per_unit_cost, expiration_date, intake_date)
-- VALUES 
--   ('101', '20', 'B-12345-TEST', 
--    50.00, 5.25, '2026-11-20', '2025-11-20');

-- CHECK:
-- This test PASSES if this command prints a "Duplicate entry" ERROR.
-- If this INSERT *succeeds*, your test has FAILED.

-- EXPECTED OUTPUT FOR TEST 2:
-- ERROR 1062 (23000): Duplicate entry '101-20-B-12345-TEST' for key 'IngredientBatch.PRIMARY'

-- =====================================================================
-- TEST FOR: trg_prevent_expired_consumption
-- =====================================================================

SELECT 'TESTING: Trigger for preventing expired consumption' AS test_name;

-- ---------------------------------------------------------------------
-- Test 1: (Happy Path) Consume a NON-expired lot.
-- This INSERT should SUCCEED.
-- ---------------------------------------------------------------------

-- ACTION:
-- We'll consume lot '101-20-B0003', which expires '2025-12-15'.
-- (Assuming CURDATE() is before that, e.g., '2025-11-15')
-- We'll consume it for Product Batch '100-MFG001-B0901'.
INSERT INTO BatchConsumption
  (product_lot_number, ingredient_lot_number, quantity_consumed)
VALUES
  ('100-MFG001-B0901', '101-20-B0003', 10.0);

-- CHECK:
-- Let's see if the row was successfully added.
SELECT * FROM BatchConsumption WHERE ingredient_lot_number = '101-20-B0003';

-- EXPECTED OUTPUT FOR TEST 1:
-- (A row is successfully returned)


-- ---------------------------------------------------------------------
-- Test 2: (Sad Path) Consume an EXPIRED lot.
-- This INSERT should FAIL.
-- It is commented out so test suite can continue
-- ---------------------------------------------------------------------

-- SELECT 'TESTING: Uniqueness constraint for lot_number' AS test_name;

-- ACTION:
-- We'll try to consume lot '101-21-B0001', which expired on '2025-10-30'.
-- (Assuming CURDATE() is after that, e.g., '2025-11-15')
-- The trigger should fire and block this INSERT.
-- INSERT INTO BatchConsumption
--   (product_lot_number, ingredient_lot_number, quantity_consumed)
-- VALUES
--   ('100-MFG001-B0901', '101-21-B0001', 5.0);

-- CHECK:
-- This test PASSES if the command above prints our custom error message.
-- If this INSERT *succeeds*, your test has FAILED.

-- EXPECTED OUTPUT FOR TEST 2:
-- ERROR 1644 (45000): ERROR: Cannot consume an expired ingredient lot! Lot has expired.

-- =====================================================================
-- TEST FOR: Master Validation & Maintain On-Hand Triggers
-- =====================================================================
-- SELECT 'TESTING: Master Validation and Maintain On-Hand Triggers' AS test_name;

-- -- ---------------------------------------------------------------------
-- -- SETUP: We need an ingredient lot that we *know* is expired.
-- -- The data in populate.sql is valid, so we'll create our own bad data.
-- -- ---------------------------------------------------------------------
-- INSERT INTO IngredientBatch 
--   (ingredient_id, supplier_id, supplier_batch_id, 
--    quantity_on_hand, per_unit_cost, expiration_date, intake_date)
-- VALUES 
--   ('101', '20', 'EXPIRED-LOT', 100.00, 5.50, '2025-01-01', '2024-01-01');

-- -- ---------------------------------------------------------------------
-- -- Test 1: (Sad Path) Try to consume the EXPIRED lot.
-- -- This tests 'trg_validate_consumption' (Check 1).
-- -- This INSERT should FAIL.
-- -- ---------------------------------------------------------------------
-- SELECT 'TESTING: (Sad Path) Consuming expired lot...' AS test_name;
-- INSERT INTO BatchConsumption
--   (product_lot_number, ingredient_lot_number, quantity_consumed)
-- VALUES
--   ('100-MFG001-B0901', '101-20-EXPIRED-LOT', 10.0);
-- EXPECTED OUTPUT: ERROR 1644 (45000): ... Lot has expired.


-- ---------------------------------------------------------------------
-- Test 2: (Sad Path) Try to consume TOO MUCH from a valid lot.
-- This tests 'trg_validate_consumption' (Check 2).
-- This INSERT should FAIL.
-- ---------------------------------------------------------------------
-- SELECT 'TESTING: (Sad Path) Consuming too much quantity...' AS test_name;

-- -- ACTION:
-- -- Lot '106-20-B0006' (from populate.sql) has 600 units.
-- -- We will try to consume 601.
-- INSERT INTO BatchConsumption
--   (product_lot_number, ingredient_lot_number, quantity_consumed)
-- VALUES
--   ('100-MFG001-B0901', '106-20-B0006', 601.0);
-- EXPECTED OUTPUT: ERROR 1644 (45000): ... Not enough quantity on hand.


-- ---------------------------------------------------------------------
-- Test 3: (Happy Path) Consume a valid amount from a valid lot.
-- ---------------------------------------------------------------------
SELECT 'TESTING: (Happy Path) Consuming valid quantity...' AS test_name;

-- CHECK (BEFORE):
-- Let's check the stock for lot '102-20-B0001'.
SELECT quantity_on_hand FROM IngredientBatch WHERE lot_number = '102-20-B0001';
-- EXPECTED OUTPUT: 600 (This is the amount *after* populate.sql ran)

-- ACTION:
-- Consume 100 units. This is valid.
INSERT INTO BatchConsumption
  (product_lot_number, ingredient_lot_number, quantity_consumed)
VALUES
  ('100-MFG001-B0901', '102-20-B0001', 100.0); -- CHANGED
-- EXPECTED OUTPUT: (Success)

-- CHECK (AFTER):
-- Let's check the stock again. It should be 100 units lower.
SELECT quantity_on_hand FROM IngredientBatch WHERE lot_number = '102-20-B0001';
-- EXPECTED OUTPUT: 500

-- ---------------------------------------------------------------------
-- Test 4: (Adjustment) "Return" the consumed items.
-- ---------------------------------------------------------------------
SELECT 'TESTING: (Adjustment) Deleting consumption record...' AS test_name;

-- ACTION:
DELETE FROM BatchConsumption
WHERE product_lot_number = '100-MFG001-B0901' 
  AND ingredient_lot_number = '102-20-B0001'; -- CHANGED
-- EXPECTED OUTPUT: (Success)

-- CHECK (FINAL):
-- Let's check the stock one last time. It should be back to 600.
SELECT quantity_on_hand FROM IngredientBatch WHERE lot_number = '102-20-B0001';
-- EXPECTED OUTPUT: 600

-- =====================================================================
-- TEST FOR: Procedure: Record_Production_Batch (ATOMICITY)
-- =====================================================================
SELECT 'TESTING: Stored Procedure Record_Production_Batch' AS test_name;

-- ---------------------------------------------------------------------
-- Test 1: (Happy Path) Create a new, valid Product Batch
-- This tests:
-- 1. The procedure itself (CALL)
-- 2. The JSON_TABLE function
-- 3. The total_batch_cost calculation
-- 4. The 'trg_validate_consumption' (Happy Path)
-- 5. The 'trg_maintain_on_hand_CONSUME' (Subtracting)
-- ---------------------------------------------------------------------
SELECT 'TESTING: (Happy Path) Calling Record_Production_Batch...' AS test_name;

-- CHECK (BEFORE):
-- Let's check the stock for the two lots we are about to consume.
-- From populate.sql, '106-20-B0005' has 3000 units.
-- From populate.sql, '201-20-B0001' has 100 units.
SELECT lot_number, quantity_on_hand 
FROM IngredientBatch 
WHERE lot_number IN ('106-20-B0005', '201-20-B0001');
-- EXPECTED:
-- '106-20-B0005', 3000.00
-- '201-20-B0001', 100.00

-- ACTION:
-- We will create a new 100-unit batch of 'Steak Dinner' (Product '100').
-- The recipe (from populate.sql) needs:
--   - '106' (Beef): 6.0 oz/unit * 100 units = 600 oz
--   - '201' (Seasoning): 0.2 oz/unit * 100 units = 20 oz
-- We'll use lots '106-20-B0005' (has 3000) and '201-20-B0001' (has 100).
SET @consumption_list = '[
    {"lot": "106-20-B0005", "qty": 600},
    {"lot": "201-20-B0001", "qty": 20}
]';

CALL Record_Production_Batch(
    '100',          -- p_product_id
    'MFG001',       -- p_manufacturer_id
    'B-TEST-001',   -- p_manufacturer_batch_id (a new, unique ID)
    100,            -- p_produced_quantity
    '2026-12-01',   -- p_expiration_date
    1,              -- p_recipe_id_used (v1-Steak-Dinner)
    @consumption_list
);
-- EXPECTED: (Success)

-- CHECK (AFTER):
-- 1. Check if the stock was correctly subtracted
SELECT lot_number, quantity_on_hand 
FROM IngredientBatch 
WHERE lot_number IN ('106-20-B0005', '201-20-B0001');
-- EXPECTED:
-- '106-20-B0005', 2400.00  (3000 - 600)
-- '201-20-B0001', 80.00    (100 - 20)

-- 2. Check if the new ProductBatch was created
--    Cost should be (600 * 0.5) + (20 * 2.5) = 300 + 50 = 350.00
SELECT lot_number, total_batch_cost 
FROM ProductBatch 
WHERE manufacturer_batch_id = 'B-TEST-001';
-- EXPECTED: '100-MFG001-B-TEST-001', 350.00

-- 3. Check if the BatchConsumption records were created
SELECT * FROM BatchConsumption 
WHERE product_lot_number = '100-MFG001-B-TEST-001';
-- EXPECTED: (2 rows returned)


-- ---------------------------------------------------------------------
-- Test 2: (Sad Path) Not Enough Quantity
-- This tests:
-- 1. The 'trg_validate_consumption' (Check 2: Quantity)
-- 2. The 'ROLLBACK' in the procedure's error handler
-- ---------------------------------------------------------------------
-- SELECT 'TESTING: (Sad Path) Not enough quantity...' AS test_name;

-- -- ACTION:
-- -- Try to create a *new* batch ('B-TEST-002')
-- -- Lot '101-20-B0003' has 500 units. We will try to consume 501.
-- SET @bad_consumption_list = '[{"lot": "101-20-B0003", "qty": 501}]';

-- CALL Record_Production_Batch(
--     '100',          -- p_product_id
--     'MFG001',       -- p_manufacturer_id
--     'B-TEST-002',   -- p_manufacturer_batch_id (a new, unique ID)
--     100,            -- p_produced_quantity
--     '2026-12-01',   -- p_expiration_date
--     1,              -- p_recipe_id_used
--     @bad_consumption_list
-- );
-- -- EXPECTED: ERROR 1644 (45000): ... Not enough quantity on hand.

-- -- CHECK (ROLLBACK):
-- -- This is the *most important check*. We must prove that
-- -- the 'B-TEST-002' batch was *NOT* created.
-- SELECT * FROM ProductBatch 
-- WHERE manufacturer_batch_id = 'B-TEST-002';
-- -- EXPECTED: (0 rows returned)


-- ---------------------------------------------------------------------
-- Test 3: (Sad Path) Expired Lot
-- This tests:
-- 1. The 'trg_validate_consumption' (Check 1: Expiration)
-- 2. The 'ROLLBACK' in the procedure's error handler
-- ---------------------------------------------------------------------
SELECT 'TESTING: (Sad Path) Expired lot...' AS test_name;

-- SETUP: Create a fake, expired lot
INSERT INTO IngredientBatch 
  (ingredient_id, supplier_id, supplier_batch_id, 
   quantity_on_hand, per_unit_cost, expiration_date, intake_date)
VALUES 
  ('101', '20', 'EXPIRED-TEST-LOT', 100, 5.0, '2025-01-01', '2024-01-01');

-- ACTION:
-- Try to create a *new* batch ('B-TEST-003') using the expired lot.
SET @expired_list = '[{"lot": "101-20-EXPIRED-TEST-LOT", "qty": 10}]';

CALL Record_Production_Batch(
    '100',          -- p_product_id
    'MFG001',        -- p_manufacturer_id
    'B-TEST-003',   -- p_manufacturer_batch_id (a new, unique ID)
    100,            -- p_produced_quantity
    '2026-12-01',   -- p_expiration_date
    1,              -- p_recipe_id_used
    @expired_list
);
-- EXPECTED: ERROR 1644 (45000): ... Lot has expired.

-- CHECK (ROLLBACK):
-- Prove that the 'B-TEST-003' batch was *NOT* created.
SELECT * FROM ProductBatch 
WHERE manufacturer_batch_id = 'B-TEST-003';
-- EXPECTED: (0 rows returned)
