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

-- ---------------------------------------------------------------------
-- Procedure: Evaluate Health Risk (FIXED for ERROR 1137)
-- This procedure "flattens" a consumption list to all its
-- atomic ingredients and checks them against the DoNotCombine table.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS Evaluate_Health_Risk;
//
CREATE PROCEDURE Evaluate_Health_Risk(
    IN p_consumption_list JSON
)
BEGIN
    DECLARE v_conflict_count INT DEFAULT 0;

    -- 1. Create temporary tables to hold our intermediate data.
    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Flattened_Atomics (
        ingredient_id VARCHAR(20) PRIMARY KEY
    );
    TRUNCATE TABLE Temp_Flattened_Atomics;

    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Affected_Lots (
        lot_number VARCHAR(255) PRIMARY KEY
    );
    TRUNCATE TABLE Temp_Affected_Lots;

    -- =================================================================
    -- FIX FOR ERROR 1137: Create a SECOND identical temp table
    -- =================================================================
    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Flattened_Atomics_2 (
        ingredient_id VARCHAR(20) PRIMARY KEY
    );
    TRUNCATE TABLE Temp_Flattened_Atomics_2;


    -- 2. Get all LOTS from the JSON
    INSERT INTO Temp_Affected_Lots (lot_number)
    SELECT lot FROM JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
        lot VARCHAR(255) PATH '$.lot'
    )) AS jt;

    -- 3. Get all ATOMIC ingredients from those lots and add them to our list
    INSERT IGNORE INTO Temp_Flattened_Atomics (ingredient_id)
    SELECT
        ib.ingredient_id
    FROM
        IngredientBatch ib
    JOIN
        Temp_Affected_Lots al ON ib.lot_number = al.lot_number
    JOIN
        Ingredient i ON ib.ingredient_id = i.ingredient_id
    WHERE
        i.ingredient_type = 'ATOMIC';

    -- 4. Get all materials from all COMPOUND ingredients and add them (the "flattening")
    INSERT IGNORE INTO Temp_Flattened_Atomics (ingredient_id)
    SELECT
        fm.material_ingredient_id
    FROM
        IngredientBatch ib
    JOIN
        Temp_Affected_Lots al ON ib.lot_number = al.lot_number
    JOIN
        Ingredient i ON ib.ingredient_id = i.ingredient_id
    -- Find the *active* formulation for this batch (based on intake date)
    JOIN
        Formulation f ON f.ingredient_id = ib.ingredient_id
        AND f.supplier_id = ib.supplier_id
        AND ib.intake_date BETWEEN f.valid_from_date AND COALESCE(f.valid_to_date, '9999-12-31')
    -- Find the materials for that formulation
    JOIN
        FormulationMaterials fm ON fm.formulation_id = f.formulation_id
    WHERE
        i.ingredient_type = 'COMPOUND';

    -- =================================================================
    -- FIX FOR ERROR 1137: Copy data from t1 into t2
    -- =================================================================
    INSERT INTO Temp_Flattened_Atomics_2 (ingredient_id)
    SELECT ingredient_id FROM Temp_Flattened_Atomics;


    -- 5. Check for conflicts
    -- We self-join our list of atomics against the DoNotCombine table
    SELECT COUNT(*)
    INTO v_conflict_count
    FROM
        Temp_Flattened_Atomics AS t1
    JOIN
        DoNotCombine AS dnc ON t1.ingredient_id = dnc.ingredient_a_id
    -- =================================================================
    -- FIX FOR ERROR 1137: Join against the *second* temp table
    -- =================================================================
    JOIN
        Temp_Flattened_Atomics_2 AS t2 ON dnc.ingredient_b_id = t2.ingredient_id;
    
    -- We also check the reverse pair (B -> A)
    SET v_conflict_count = v_conflict_count + (
        SELECT COUNT(*)
        FROM
            Temp_Flattened_Atomics AS t1
        JOIN
            DoNotCombine AS dnc ON t1.ingredient_id = dnc.ingredient_b_id
        -- =================================================================
        -- FIX FOR ERROR 1137: Join against the *second* temp table
        -- =================================================================
        JOIN
            Temp_Flattened_Atomics_2 AS t2 ON dnc.ingredient_a_id = t2.ingredient_id
    );

    -- 6. Block or Allow
    IF v_conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Health risk detected! Incompatible ingredients found in batch.';
    END IF;
    -- If count is 0, the procedure finishes successfully.
    -- Temporary tables are dropped automatically when the session ends.

END;
//

-- ---------------------------------------------------------------------
-- Procedure: Record Production Batch
-- This is the main "engine" of the application. It atomically
-- creates a new product batch and consumes all specified ingredients.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS Record_Production_Batch;
//
CREATE PROCEDURE Record_Production_Batch(
    -- IN parameters are data we pass *into* the procedure
    IN p_product_id VARCHAR(20),
    IN p_manufacturer_id VARCHAR(20),
    IN p_manufacturer_batch_id VARCHAR(100),
    IN p_produced_quantity INT,
    IN p_expiration_date DATE,
    IN p_recipe_id_used INT,
    IN p_consumption_list JSON -- e.g., '[{"lot": "106-20-B0006", "qty": 600}, ...]'
)
BEGIN
    -- == 1. DECLARE VARIABLES ==
    -- We'll store the calculated cost and new lot number here
    DECLARE v_total_cost DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_new_lot_number VARCHAR(255);

    -- == 2. ERROR HANDLER ==
    -- This is the "safety net". If *any* SQL error occurs (like
    -- our triggers failing), this handler will catch it.
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        -- An error occurred! Undo *all* changes.
        ROLLBACK;
        -- Pass the error message back up to the Python app
        RESIGNAL;
    END;

    -- == 3. START TRANSACTION ==
    -- This is the "safety bubble". All or nothing.
    START TRANSACTION;
    
    -- =================================================================
    -- NEW STEP 3.5: CHECK FOR HEALTH RISKS BEFORE DOING ANYTHING ELSE
    -- =================================================================
    CALL Evaluate_Health_Risk(p_consumption_list);
    -- If the above line throws an error (conflict detected), 
    -- the EXIT HANDLER will catch it, ROLLBACK, and stop execution.
    -- If no error, we continue...
    
    -- == 4. CALCULATE TOTAL COST ==
    -- We use JSON_TABLE to turn the JSON array into a temporary table
    -- which we can JOIN with IngredientBatch to calculate the cost.
    SELECT SUM(jt.qty * ib.per_unit_cost)
    INTO v_total_cost
    FROM 
      JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
          lot VARCHAR(255) PATH '$.lot',
          qty DECIMAL(10, 2) PATH '$.qty'
      )) AS jt
    JOIN 
      IngredientBatch AS ib ON ib.lot_number = jt.lot;

    -- == 5. CREATE THE FINISHED GOODS (PRODUCT BATCH) ==
    -- We insert the new product batch into the table.
    -- Our 'trg_compute_product_lot_number' will fire automatically.
    INSERT INTO ProductBatch
      (product_id, manufacturer_id, manufacturer_batch_id, 
       produced_quantity, production_date, expiration_date, 
       recipe_id_used, total_batch_cost)
    VALUES
      (p_product_id, p_manufacturer_id, p_manufacturer_batch_id,
       p_produced_quantity, CURDATE(), p_expiration_date,
       p_recipe_id_used, v_total_cost);

    -- == 6. CONSUME THE INGREDIENTS ==
    -- We need the new lot number to link to the consumption records.
    -- We can re-build it because we have all the parts.
    SET v_new_lot_number = CONCAT(p_product_id, '-', p_manufacturer_id, '-', p_manufacturer_batch_id);

    -- Now, insert all consumption records.
    -- Our 'trg_validate_consumption' (BEFORE) and
    -- 'trg_maintain_on_hand_CONSUME' (AFTER) will fire
    -- automatically for *each row* this INSERT creates.
    INSERT INTO BatchConsumption
      (product_lot_number, ingredient_lot_number, quantity_consumed)
    SELECT
      v_new_lot_number, -- The new lot number we just created
      jt.lot,           -- The 'lot' column from the JSON
      jt.qty            -- The 'qty' column from the JSON
    FROM 
      JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
          lot VARCHAR(255) PATH '$.lot',
          qty DECIMAL(10, 2) PATH '$.qty'
      )) AS jt;

    -- == 7. COMMIT ==
    -- If we made it this far, it means no errors occurred.
    -- We exit the "safety bubble" and make all changes permanent.
    COMMIT;

END;
//

-- ---------------------------------------------------------------------
-- Procedure: Trace Recall
-- This procedure finds all product batches affected by a
-- specific recalled ingredient lot, within a 20-day window.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS Trace_Recall;
//
CREATE PROCEDURE Trace_Recall(
    IN p_ingredient_lot_number VARCHAR(255), -- The lot ID to recall
    IN p_recall_date DATE                    -- The date the recall was issued
)
BEGIN
    -- This query joins the consumption link to the batch and product tables.
    SELECT
        pb.lot_number AS affected_product_lot,
        p.name AS product_name,
        pb.production_date,
        pb.expiration_date,
        pb.produced_quantity
    FROM
        BatchConsumption AS bc
    JOIN
        ProductBatch AS pb ON bc.product_lot_number = pb.lot_number
    JOIN
        Product AS p ON pb.product_id = p.product_id
    WHERE
        -- 1. Find the specific recalled ingredient lot
        bc.ingredient_lot_number = p_ingredient_lot_number
        
        -- 2. Filter by the 20-day time window
        -- We check if the production_date (a DATETIME) is between
        -- 20 days *before* the recall date and the recall date itself.
        AND DATE(pb.production_date) 
            BETWEEN (p_recall_date - INTERVAL 20 DAY) AND p_recall_date;

END;
//

DELIMITER ;