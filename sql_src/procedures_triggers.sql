-- ============================================
-- STORED PROCEDURES AND TRIGGERS
-- Meal Manufacturer Database
-- ============================================

USE Meal_Manufacturer;

-- ============================================
-- TRIGGERS
-- ============================================

-- ============================================
-- LOT NUMBER TRIGGERS
-- ============================================

DROP TRIGGER IF EXISTS trg_compute_ingredient_lot_number;

DELIMITER //
CREATE TRIGGER trg_compute_ingredient_lot_number
BEFORE INSERT ON IngredientBatch
FOR EACH ROW
BEGIN
  SET NEW.lot_number = CONCAT(
    NEW.ingredient_id, 
    '-', 
    NEW.supplier_id, 
    '-', 
    NEW.supplier_batch_id
  );
END;
//

DROP TRIGGER IF EXISTS trg_compute_product_lot_number;

CREATE TRIGGER trg_compute_product_lot_number
BEFORE INSERT ON ProductBatch
FOR EACH ROW
BEGIN
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
AFTER INSERT ON BatchConsumption
FOR EACH ROW
BEGIN
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
AFTER DELETE ON BatchConsumption
FOR EACH ROW
BEGIN
    UPDATE IngredientBatch
    SET quantity_on_hand = quantity_on_hand + OLD.quantity_consumed
    WHERE lot_number = OLD.ingredient_lot_number;
END;
//

-- ---------------------------------------------------------------------
-- Procedure: Evaluate Health Risk
-- Flattens consumption list and validates against DoNotCombine table
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS Evaluate_Health_Risk;
//
CREATE PROCEDURE Evaluate_Health_Risk(
    IN p_consumption_list JSON
)
BEGIN
    DECLARE v_conflict_count INT DEFAULT 0;

    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Flattened_Atomics (
        ingredient_id VARCHAR(20) PRIMARY KEY
    );
    TRUNCATE TABLE Temp_Flattened_Atomics;

    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Affected_Lots (
        lot_number VARCHAR(255) PRIMARY KEY
    );
    TRUNCATE TABLE Temp_Affected_Lots;

    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Flattened_Atomics_2 (
        ingredient_id VARCHAR(20) PRIMARY KEY
    );
    TRUNCATE TABLE Temp_Flattened_Atomics_2;

    -- Get all lots from the JSON
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
    
    SET v_conflict_count = v_conflict_count + (
        SELECT COUNT(*)
        FROM
            Temp_Flattened_Atomics AS t1
        JOIN
            DoNotCombine AS dnc ON t1.ingredient_id = dnc.ingredient_b_id
        JOIN
            Temp_Flattened_Atomics_2 AS t2 ON dnc.ingredient_a_id = t2.ingredient_id
    );

    -- 6. Block or Allow
    IF v_conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Health risk detected! Incompatible ingredients found in batch.';
    END IF;

END;
//

-- ---------------------------------------------------------------------
-- Procedure: Record Production Batch
-- Main transaction for creating a product batch and consuming ingredients
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS Record_Production_Batch;
//
CREATE PROCEDURE Record_Production_Batch(
    IN p_product_id VARCHAR(20),
    IN p_manufacturer_id VARCHAR(20),
    IN p_manufacturer_batch_id VARCHAR(100),
    IN p_produced_quantity INT,
    IN p_expiration_date DATE,
    IN p_recipe_id_used INT,
    IN p_consumption_list JSON
)
BEGIN
    DECLARE v_total_cost DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_new_lot_number VARCHAR(255);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
    
    CALL Evaluate_Health_Risk(p_consumption_list);
    
    -- Calculate total cost using consumption list
    SELECT SUM(jt.qty * ib.per_unit_cost)
    INTO v_total_cost
    FROM 
      JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
          lot VARCHAR(255) PATH '$.lot',
          qty DECIMAL(10, 2) PATH '$.qty'
      )) AS jt
    JOIN 
      IngredientBatch AS ib ON ib.lot_number = jt.lot;

    -- Create product batch record
    INSERT INTO ProductBatch
      (product_id, manufacturer_id, manufacturer_batch_id, 
       produced_quantity, production_date, expiration_date, 
       recipe_id_used, total_batch_cost)
    VALUES
      (p_product_id, p_manufacturer_id, p_manufacturer_batch_id,
       p_produced_quantity, CURDATE(), p_expiration_date,
       p_recipe_id_used, v_total_cost);

    -- Record ingredient consumption
    SET v_new_lot_number = CONCAT(p_product_id, '-', p_manufacturer_id, '-', p_manufacturer_batch_id);

    INSERT INTO BatchConsumption
      (product_lot_number, ingredient_lot_number, quantity_consumed)
    SELECT
      v_new_lot_number,
      jt.lot,
      jt.qty
    FROM 
      JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
          lot VARCHAR(255) PATH '$.lot',
          qty DECIMAL(10, 2) PATH '$.qty'
      )) AS jt;

    COMMIT;

END;
//

-- ---------------------------------------------------------------------
-- Procedure: Trace Recall
-- Find all product batches affected by a recalled ingredient lot
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS Trace_Recall;
//
CREATE PROCEDURE Trace_Recall(
    IN p_ingredient_lot_number VARCHAR(255),
    IN p_recall_date DATE
)
BEGIN
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
        bc.ingredient_lot_number = p_ingredient_lot_number
        AND DATE(pb.production_date) 
            BETWEEN (p_recall_date - INTERVAL 20 DAY) AND p_recall_date;

END;
//

DELIMITER ;