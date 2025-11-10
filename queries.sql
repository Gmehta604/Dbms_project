-- CSC540 Project 1: Inventory Management System
-- Required Queries Implementation
-- Database: MariaDB/MySQL

USE csc_540;

-- ============================================================================
-- REQUIRED QUERIES
-- ============================================================================

-- Query 1: List the ingredients and the lot number of the last batch of 
--          product type Steak Dinner (100) made by manufacturer MFG001
-- Assumptions: product_id = 100 is "Steak Dinner", manufacturer_id = 1 is "MFG001"
-- Note: In actual implementation, these would be looked up by name

SELECT 
    i.ingredient_id,
    i.ingredient_name,
    ib.lot_number AS ingredient_lot_number,
    bc.quantity_used
FROM PRODUCT_BATCHES pb
INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
INNER JOIN INGREDIENTS i ON ib.ingredient_id = i.ingredient_id
WHERE p.product_id = 100
  AND m.manufacturer_id = 1
  AND pb.production_date = (
      SELECT MAX(pb2.production_date)
      FROM PRODUCT_BATCHES pb2
      INNER JOIN PRODUCTS p2 ON pb2.product_id = p2.product_id
      WHERE p2.product_id = 100
        AND p2.manufacturer_id = 1
  )
ORDER BY i.ingredient_name;

-- Alternative version using product name and manufacturer name lookup:
-- SELECT 
--     i.ingredient_id,
--     i.ingredient_name,
--     ib.lot_number AS ingredient_lot_number,
--     bc.quantity_used
-- FROM PRODUCT_BATCHES pb
-- INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
-- INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
-- INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
-- INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
-- INNER JOIN INGREDIENTS i ON ib.ingredient_id = i.ingredient_id
-- WHERE p.product_name = 'Steak Dinner'
--   AND m.manufacturer_name = 'MFG001'
--   AND pb.production_date = (
--       SELECT MAX(pb2.production_date)
--       FROM PRODUCT_BATCHES pb2
--       INNER JOIN PRODUCTS p2 ON pb2.product_id = p2.product_id
--       INNER JOIN MANUFACTURERS m2 ON p2.manufacturer_id = m2.manufacturer_id
--       WHERE p2.product_name = 'Steak Dinner'
--         AND m2.manufacturer_name = 'MFG001'
--   )
-- ORDER BY i.ingredient_name;


-- Query 2: For manufacturer MFG002, list all the suppliers that they have 
--          purchased from and the total amount of money they have spent with that supplier
-- Assumption: manufacturer_id = 2 is "MFG002"

SELECT 
    s.supplier_id,
    s.supplier_name,
    SUM(bc.quantity_used * ib.cost_per_unit) AS total_amount_spent
FROM MANUFACTURERS m
INNER JOIN PRODUCTS p ON m.manufacturer_id = p.manufacturer_id
INNER JOIN PRODUCT_BATCHES pb ON p.product_id = pb.product_id
INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
INNER JOIN SUPPLIERS s ON ib.supplier_id = s.supplier_id
WHERE m.manufacturer_id = 2
GROUP BY s.supplier_id, s.supplier_name
ORDER BY total_amount_spent DESC;

-- Alternative version using manufacturer name lookup:
-- SELECT 
--     s.supplier_id,
--     s.supplier_name,
--     SUM(bc.quantity_used * ib.cost_per_unit) AS total_amount_spent
-- FROM MANUFACTURERS m
-- INNER JOIN PRODUCTS p ON m.manufacturer_id = p.manufacturer_id
-- INNER JOIN PRODUCT_BATCHES pb ON p.product_id = pb.product_id
-- INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
-- INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
-- INNER JOIN SUPPLIERS s ON ib.supplier_id = s.supplier_id
-- WHERE m.manufacturer_name = 'MFG002'
-- GROUP BY s.supplier_id, s.supplier_name
-- ORDER BY total_amount_spent DESC;


-- Query 3: For product with lot number 100-MFG001-B0901, find the unit cost for that product
-- Note: Batch number format in database is <productId>-<manufacturerId>-B<batchId>
--       where manufacturerId is numeric. For lookup by name, we join with manufacturers table.

SELECT 
    pb.batch_number,
    pb.cost_per_unit,
    pb.total_cost,
    pb.quantity_produced,
    p.product_name,
    m.manufacturer_name
FROM PRODUCT_BATCHES pb
INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
WHERE CONCAT(pb.product_id, '-', m.manufacturer_name, '-B', SUBSTRING_INDEX(pb.batch_number, 'B', -1)) = '100-MFG001-B0901'
   OR pb.batch_number = '100-1-B0901';  -- Also check direct format


-- Query 4: Based on the ingredients currently in product lot number 100-MFG001-B0901, 
--          what are all ingredients that cannot be included (i.e. that are in conflict 
--          with the current ingredient list)

-- First, get all ingredients in the product batch (including nested materials)
WITH product_ingredients AS (
    -- Direct ingredients from the batch
    SELECT DISTINCT ib.ingredient_id
    FROM PRODUCT_BATCHES pb
    INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
    INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
    INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
    INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
    WHERE (CONCAT(pb.product_id, '-', m.manufacturer_name, '-B', SUBSTRING_INDEX(pb.batch_number, 'B', -1)) = '100-MFG001-B0901'
       OR pb.batch_number = '100-1-B0901')
    
    UNION
    
    -- Nested materials (one level) from compound ingredients
    SELECT DISTINCT ic.child_ingredient_id
    FROM PRODUCT_BATCHES pb
    INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
    INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
    INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
    INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
    INNER JOIN INGREDIENT_COMPOSITIONS ic ON ib.ingredient_id = ic.parent_ingredient_id
    WHERE (CONCAT(pb.product_id, '-', m.manufacturer_name, '-B', SUBSTRING_INDEX(pb.batch_number, 'B', -1)) = '100-MFG001-B0901'
       OR pb.batch_number = '100-1-B0901')
)
SELECT DISTINCT
    i.ingredient_id,
    i.ingredient_name,
    dnc.reason AS conflict_reason
FROM DO_NOT_COMBINE dnc
INNER JOIN INGREDIENTS i ON (
    (dnc.ingredient1_id = i.ingredient_id AND dnc.ingredient2_id IN (SELECT ingredient_id FROM product_ingredients))
    OR (dnc.ingredient2_id = i.ingredient_id AND dnc.ingredient1_id IN (SELECT ingredient_id FROM product_ingredients))
)
WHERE dnc.ingredient1_id IN (SELECT ingredient_id FROM product_ingredients)
   OR dnc.ingredient2_id IN (SELECT ingredient_id FROM product_ingredients)
ORDER BY i.ingredient_name;


-- Query 5: Which manufacturers have supplier James Miller (21) NOT supplied to?
-- Assumption: supplier_id = 21 is "James Miller"

-- Get all manufacturers
SELECT 
    m.manufacturer_id,
    m.manufacturer_name
FROM MANUFACTURERS m
WHERE m.manufacturer_id NOT IN (
    -- Manufacturers that HAVE been supplied by James Miller (supplier_id = 21)
    SELECT DISTINCT p.manufacturer_id
    FROM PRODUCTS p
    INNER JOIN PRODUCT_BATCHES pb ON p.product_id = pb.product_id
    INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
    INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
    WHERE ib.supplier_id = 21
)
ORDER BY m.manufacturer_name;

-- Alternative version using supplier name lookup:
-- SELECT 
--     m.manufacturer_id,
--     m.manufacturer_name
-- FROM MANUFACTURERS m
-- WHERE m.manufacturer_id NOT IN (
--     SELECT DISTINCT p.manufacturer_id
--     FROM PRODUCTS p
--     INNER JOIN PRODUCT_BATCHES pb ON p.product_id = pb.product_id
--     INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
--     INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
--     INNER JOIN SUPPLIERS s ON ib.supplier_id = s.supplier_id
--     WHERE s.supplier_name = 'James Miller'
-- )
-- ORDER BY m.manufacturer_name;

