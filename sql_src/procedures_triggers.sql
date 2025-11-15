-- ============================================
-- STORED PROCEDURES AND TRIGGERS
-- Meal Manufacturer Database
-- ============================================

USE Meal_Manufacturer;

-- ============================================
-- TRIGGERS
-- ============================================

-- Drop the trigger if it already exists to prevent an error
DROP TRIGGER IF EXISTS trg_compute_ingredient_lot_number;

DELIMITER //
CREATE TRIGGER trg_compute_ingredient_lot_number
-- This specifies that the trigger runs *before* the INSERT operation
BEFORE INSERT ON IngredientBatch
-- This means the trigger runs for each individual row being inserted
FOR EACH ROW
BEGIN
  -- 'NEW' is a special keyword that refers to the row that is *about*
  -- to be inserted into the table.
  
  -- We set the 'lot_number' column of the new row by concatenating
  -- the three "part" columns with hyphens.
  SET NEW.lot_number = CONCAT(
    NEW.ingredient_id, 
    '-', 
    NEW.supplier_id, 
    '-', 
    NEW.supplier_batch_id
  );
END;
//

-- Drop the trigger if it already exists to prevent an error
DROP TRIGGER IF EXISTS trg_compute_product_lot_number;

CREATE TRIGGER trg_compute_product_lot_number
-- This trigger fires *before* a new row is saved
BEFORE INSERT ON ProductBatch
-- This means the trigger runs for each individual row being inserted
FOR EACH ROW
BEGIN
  -- 'NEW' refers to the row that is *about* to be inserted.
  
  -- We set the 'lot_number' column by concatenating the "parts"
  -- just like we did for the ingredient batch.
  SET NEW.lot_number = CONCAT(
    NEW.product_id, 
    '-', 
    NEW.manufacturer_id, 
    '-', 
    NEW.manufacturer_batch_id
  );
END;
//

DELIMITER ;