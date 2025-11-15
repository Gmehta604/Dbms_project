-- ============================================
-- STORED PROCEDURES AND TRIGGERS
-- Meal Manufacturer Database
-- ============================================

USE Meal_Manufacturer;

-- ============================================
-- TRIGGERS
-- ============================================

-- ============================================
-- LOT NUMBER TRIGGERS (Completed)
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

-- ============================================
-- MASTER CONSUMPTION VALIDATION TRIGGER (UPDATED)
-- ============================================

-- Drop the old trigger
DROP TRIGGER IF EXISTS trg_prevent_expired_consumption;
-- Drop the new trigger if it exists
DROP TRIGGER IF EXISTS trg_validate_consumption;
//
CREATE TRIGGER trg_validate_consumption
-- Fire *before* a consumption record is saved
BEFORE INSERT ON BatchConsumption
FOR EACH ROW
BEGIN
    -- 1. Create variables to hold the data we need to check
    DECLARE v_expiration_date DATE;
    DECLARE v_quantity_on_hand DECIMAL(10, 2);

    -- 2. Look up the batch data from the 'parent' table
    SELECT expiration_date, quantity_on_hand INTO v_expiration_date, v_quantity_on_hand
    FROM IngredientBatch
    WHERE lot_number = NEW.ingredient_lot_number;

    -- 3. CHECK 1: Is the lot expired?
    IF CURDATE() > v_expiration_date THEN
        -- If it is expired, stop the INSERT and throw a custom error.
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Cannot consume an expired ingredient lot! Lot has expired.';
    END IF;
    
    -- 4. CHECK 2: Is there enough quantity?
    IF v_quantity_on_hand < NEW.quantity_consumed THEN
        -- If not enough stock, stop the INSERT and throw a custom error.
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Not enough quantity on hand. A-vailable: v_quantity_on_hand, Tried to consume: NEW.quantity_consumed';
    END IF;
    
    -- If both checks pass, the trigger finishes and the INSERT proceeds.
END;
//

-- ============================================
-- MAINTAIN ON-HAND TRIGGERS (NEWLY ADDED)
-- ============================================

-- ---------------------------------------------------------------------
-- Trigger 1: "Consumption"
-- This trigger fires *after* a consumption record is inserted
-- and SUBTRACTS the quantity from the ingredient batch.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_maintain_on_hand_CONSUME;
//
CREATE TRIGGER trg_maintain_on_hand_CONSUME
-- We use AFTER INSERT. This now fires *after* our
-- 'trg_validate_consumption' (BEFORE INSERT) has passed,
-- so we know this subtraction is 100% safe.
AFTER INSERT ON BatchConsumption
FOR EACH ROW
BEGIN
    -- 'NEW' refers to the row that was just inserted
    -- This UPDATE finds the matching IngredientBatch and subtracts
    -- the consumed quantity from its on_hand balance.
    UPDATE IngredientBatch
    SET quantity_on_hand = quantity_on_hand - NEW.quantity_consumed
    WHERE lot_number = NEW.ingredient_lot_number;
END;
//

-- ---------------------------------------------------------------------
-- Trigger 2: "Adjustment"
-- This trigger fires *after* a consumption record is deleted
-- and ADDS the quantity *back* to the ingredient batch.
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_maintain_on_hand_ADJUST;
//
CREATE TRIGGER trg_maintain_on_hand_ADJUST
-- This fires after a row is successfully deleted
AFTER DELETE ON BatchConsumption
FOR EACH ROW
BEGIN
    -- 'OLD' is a special keyword that refers to the row
    -- that was just deleted.
    -- This UPDATE finds the matching IngredientBatch and adds
    -- the *previously consumed* quantity back to its on_hand balance.
    UPDATE IngredientBatch
    SET quantity_on_hand = quantity_on_hand + OLD.quantity_consumed
    WHERE lot_number = OLD.ingredient_lot_number;
END;
//


DELIMITER ;