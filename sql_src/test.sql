DROP DATABASE IF EXISTS Meal_Manufacturer;
CREATE DATABASE Meal_Manufacturer;
USE Meal_Manufacturer;

SOURCE sql_src/schema.sql;
SOURCE sql_src/procedures_triggers.sql;
SOURCE sql_src/data.sql;

-- =====================================================================
-- TEST: Ingredient Lot Number Trigger
-- =====================================================================

SELECT 'Testing: Ingredient lot number creation' AS test_name;

INSERT INTO IngredientBatch 
  (ingredient_id, supplier_id, supplier_batch_id, 
   quantity_on_hand, per_unit_cost, expiration_date, intake_date)
VALUES 
  ('101', '20', 'B-12345-TEST', 
   100.00, 5.50, '2026-11-15', '2025-11-15');

SELECT lot_number 
FROM IngredientBatch 
WHERE supplier_batch_id = 'B-12345-TEST';

-- =====================================================================
-- TEST: Prevent Expired Consumption Trigger
-- =====================================================================

SELECT 'Testing: Expired consumption prevention' AS test_name;

INSERT INTO BatchConsumption
  (product_lot_number, ingredient_lot_number, quantity_consumed)
VALUES
  ('100-MFG001-B0901', '101-20-B0003', 10.0);

SELECT * FROM BatchConsumption WHERE ingredient_lot_number = '101-20-B0003';

-- =====================================================================
-- TEST: Validation and Inventory Maintenance Triggers
-- =====================================================================

SELECT 'Testing: Validation and inventory maintenance' AS test_name;

SELECT quantity_on_hand FROM IngredientBatch WHERE lot_number = '102-20-B0001';

INSERT INTO BatchConsumption
  (product_lot_number, ingredient_lot_number, quantity_consumed)
VALUES
  ('100-MFG001-B0901', '102-20-B0001', 100.0);

SELECT quantity_on_hand FROM IngredientBatch WHERE lot_number = '102-20-B0001';

-- Test adjustment (delete) trigger
DELETE FROM BatchConsumption
WHERE product_lot_number = '100-MFG001-B0901' 
  AND ingredient_lot_number = '102-20-B0001';

SELECT quantity_on_hand FROM IngredientBatch WHERE lot_number = '102-20-B0001';

-- =====================================================================
-- TEST: Record Production Batch Procedure
-- =====================================================================

SELECT 'Testing: Record Production Batch procedure' AS test_name;

SELECT lot_number, quantity_on_hand 
FROM IngredientBatch 
WHERE lot_number IN ('106-20-B0005', '201-20-B0001');

SET @consumption_list = '[
    {"lot": "106-20-B0005", "qty": 600},
    {"lot": "201-20-B0001", "qty": 20}
]';

CALL Record_Production_Batch(
    '100',
    'MFG001',
    'B-TEST-001',
    100,
    '2026-12-01',
    1,
    @consumption_list
);

SELECT lot_number, quantity_on_hand 
FROM IngredientBatch 
WHERE lot_number IN ('106-20-B0005', '201-20-B0001');

SELECT lot_number, total_batch_cost 
FROM ProductBatch 
WHERE manufacturer_batch_id = 'B-TEST-001';

SELECT * FROM BatchConsumption 
WHERE product_lot_number = '100-MFG001-B-TEST-001';

-- =====================================================================
-- TEST: Trace Recall Procedure
-- =====================================================================

SELECT 'Testing: Trace Recall procedure' AS test_name;

-- Test 1: Item within recall window
CALL Trace_Recall(
    '106-20-B0006',
    '2025-09-30'
);

-- Test 2: Item outside recall window
CALL Trace_Recall(
    '106-20-B0006',
    '2025-10-20'
);

-- Test 3: Item never consumed
CALL Trace_Recall(
    '101-20-B0001',
    '2025-12-01'
);

-- =====================================================================
-- TEST: Evaluate Health Risk Procedure
-- =====================================================================

SELECT 'Testing: Evaluate Health Risk procedure' AS test_name;

-- Test 1: No conflicts
SET @safe_list = '[
    {"lot": "106-20-B0006", "qty": 600},
    {"lot": "201-20-B0002", "qty": 20}
]';

CALL Evaluate_Health_Risk(@safe_list);

-- Test 2: Conflict in compound ingredient
INSERT INTO Ingredient (ingredient_id, name, ingredient_type) 
  VALUES ('C-104', 'Phosphate Blend', 'COMPOUND');

INSERT INTO Formulation 
  (formulation_id, ingredient_id, supplier_id, valid_from_date, unit_price, pack_size) 
  VALUES (2, 'C-104', '20', '2025-01-01', 10.0, '1kg');

INSERT INTO FormulationMaterials 
  (formulation_id, material_ingredient_id, quantity) 
  VALUES (2, '104', 5.0);

INSERT INTO IngredientBatch 
  (ingredient_id, supplier_id, supplier_batch_id, 
   quantity_on_hand, per_unit_cost, expiration_date, intake_date)
VALUES 
  ('C-104', '20', 'B-PHOS-BLEND', 100.00, 10.0, '2026-11-15', '2025-11-15');

SET @compound_conflict_list = '[
    {"lot": "106-20-B0006", "qty": 10},
    {"lot": "C-104-20-B-PHOS-BLEND", "qty": 10}
]';

-- This should fail with health risk error
CALL Evaluate_Health_Risk(@compound_conflict_list);
