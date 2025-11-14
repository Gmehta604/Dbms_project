-- ============================================
-- STORED PROCEDURES AND TRIGGERS
-- Meal Manufacturer Database
-- ============================================

USE Meal_Manufacturer;

-- ============================================
-- TRIGGERS
-- ============================================

-- Trigger 1: Compute Ingredient Lot Number on insert
-- Enforces format: ingredientId-supplierId-batchId
DELIMITER //

DROP TRIGGER IF EXISTS trg_ingredient_batch_lot_number//
CREATE TRIGGER trg_ingredient_batch_lot_number
BEFORE INSERT ON Ingredient_Batches
FOR EACH ROW
BEGIN
    DECLARE expected_lot VARCHAR(100);
    
    -- Generate expected lot number format: ingredientId-supplierId-batchId
    -- Extract batch ID from the provided lot_number (assuming format is correct)
    -- If lot_number doesn't match expected format, generate it
    SET expected_lot = CONCAT(NEW.ingredient_id, '-', NEW.supplier_id, '-', 
                              SUBSTRING_INDEX(NEW.lot_number, '-', -1));
    
    -- Validate format matches expected pattern
    IF NEW.lot_number NOT REGEXP CONCAT('^', NEW.ingredient_id, '-', NEW.supplier_id, '-[A-Z0-9]+$') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Lot number format must be: ingredientId-supplierId-batchId';
    END IF;
    
    -- Check uniqueness
    IF EXISTS (SELECT 1 FROM Ingredient_Batches WHERE lot_number = NEW.lot_number) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Lot number already exists';
    END IF;
END//

-- Trigger 2: Prevent Expired Consumption
DROP TRIGGER IF EXISTS trg_prevent_expired_consumption//
CREATE TRIGGER trg_prevent_expired_consumption
BEFORE INSERT ON Batch_Consumption
FOR EACH ROW
BEGIN
    DECLARE exp_date DATE;
    
    -- Get expiration date of the ingredient lot
    SELECT expiration_date INTO exp_date
    FROM Ingredient_Batches
    WHERE lot_number = NEW.ingredient_lot_number;
    
    -- Check if expired
    IF exp_date IS NOT NULL AND exp_date < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot consume expired ingredient lot';
    END IF;
END//

-- Trigger 3: Maintain On-Hand Inventory
-- This trigger automatically updates inventory when batches are received
-- Note: Consumption updates are handled in the application/procedure

DROP TRIGGER IF EXISTS trg_maintain_on_hand_receipt//
CREATE TRIGGER trg_maintain_on_hand_receipt
BEFORE INSERT ON Ingredient_Batches
FOR EACH ROW
BEGIN
    -- On insert, quantity_on_hand is set directly, so this trigger just validates
    IF NEW.quantity_on_hand < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantity on hand cannot be negative';
    END IF;
END//

-- ============================================
-- STORED PROCEDURES
-- ============================================

-- Procedure 1: Record Production Batch
-- Creates batch, consumes ingredient lots atomically, computes cost
DROP PROCEDURE IF EXISTS RecordProductionBatch//
CREATE PROCEDURE RecordProductionBatch(
    IN p_batch_number VARCHAR(100),
    IN p_product_id INT,
    IN p_plan_id INT,
    IN p_quantity_produced INT,
    IN p_production_date DATE,
    IN p_expiration_date DATE,
    OUT p_total_cost DECIMAL(12,2),
    OUT p_cost_per_unit DECIMAL(12,2),
    OUT p_success BOOLEAN
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_success = FALSE;
        RESIGNAL;
    END;
    
    DECLARE v_total_cost DECIMAL(12,2) DEFAULT 0;
    DECLARE v_cost_per_unit DECIMAL(12,2) DEFAULT 0;
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_lot_number VARCHAR(100);
    DECLARE v_quantity_used DECIMAL(10,2);
    DECLARE v_cost_per_unit_lot DECIMAL(10,2);
    DECLARE v_lot_cost DECIMAL(12,2);
    
    -- Cursor for batch consumption records
    DECLARE cur_consumption CURSOR FOR
        SELECT ingredient_lot_number, quantity_used
        FROM Batch_Consumption
        WHERE product_batch_number = p_batch_number;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    START TRANSACTION;
    
    -- Calculate total cost from consumption records
    OPEN cur_consumption;
    read_loop: LOOP
        FETCH cur_consumption INTO v_lot_number, v_quantity_used;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Get cost per unit for this lot
        SELECT cost_per_unit INTO v_cost_per_unit_lot
        FROM Ingredient_Batches
        WHERE lot_number = v_lot_number;
        
        SET v_lot_cost = v_quantity_used * v_cost_per_unit_lot;
        SET v_total_cost = v_total_cost + v_lot_cost;
        
        -- Update lot quantity
        UPDATE Ingredient_Batches
        SET quantity_on_hand = quantity_on_hand - v_quantity_used
        WHERE lot_number = v_lot_number;
        
        -- Validate quantity
        IF (SELECT quantity_on_hand FROM Ingredient_Batches WHERE lot_number = v_lot_number) < 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Insufficient quantity in lot';
        END IF;
    END LOOP;
    CLOSE cur_consumption;
    
    -- Calculate cost per unit
    IF p_quantity_produced > 0 THEN
        SET v_cost_per_unit = v_total_cost / p_quantity_produced;
    END IF;
    
    -- Insert product batch
    INSERT INTO Product_Batches (
        batch_number, product_id, plan_id, quantity_produced,
        total_cost, cost_per_unit, production_date, expiration_date
    ) VALUES (
        p_batch_number, p_product_id, p_plan_id, p_quantity_produced,
        v_total_cost, v_cost_per_unit, p_production_date, p_expiration_date
    );
    
    SET p_total_cost = v_total_cost;
    SET p_cost_per_unit = v_cost_per_unit;
    SET p_success = TRUE;
    
    COMMIT;
END//

-- Procedure 2: Trace Recall
-- Given ingredient ID or lot number, find affected product batches
DROP PROCEDURE IF EXISTS TraceRecall//
CREATE PROCEDURE TraceRecall(
    IN p_identifier VARCHAR(100)
)
BEGIN
    -- Try to determine if identifier is ingredient_id or lot_number
    -- If it's numeric and short, assume ingredient_id; otherwise assume lot_number
    
    IF p_identifier REGEXP '^[0-9]+$' AND LENGTH(p_identifier) <= 5 THEN
        -- Assume ingredient_id
        SELECT DISTINCT
            pb.batch_number,
            p.product_name,
            pb.production_date,
            pb.quantity_produced
        FROM Product_Batches pb
        JOIN Products p ON pb.product_id = p.product_id
        JOIN Batch_Consumption bc ON pb.batch_number = bc.product_batch_number
        JOIN Ingredient_Batches ib ON bc.ingredient_lot_number = ib.lot_number
        WHERE ib.ingredient_id = CAST(p_identifier AS UNSIGNED)
           OR ib.ingredient_id IN (
               SELECT child_ingredient_id
               FROM Ingredient_Compositions
               WHERE parent_ingredient_id = CAST(p_identifier AS UNSIGNED)
           )
        ORDER BY pb.production_date DESC;
    ELSE
        -- Assume lot_number
        SELECT DISTINCT
            pb.batch_number,
            p.product_name,
            pb.production_date,
            pb.quantity_produced
        FROM Product_Batches pb
        JOIN Products p ON pb.product_id = p.product_id
        JOIN Batch_Consumption bc ON pb.batch_number = bc.product_batch_number
        WHERE bc.ingredient_lot_number = p_identifier
        ORDER BY pb.production_date DESC;
    END IF;
END//

-- Procedure 3: Evaluate Health Risk
-- Checks for do-not-combine conflicts when creating a batch
DROP PROCEDURE IF EXISTS EvaluateHealthRisk//
CREATE PROCEDURE EvaluateHealthRisk(
    IN p_batch_number VARCHAR(100),
    OUT p_has_conflict BOOLEAN,
    OUT p_conflict_count INT
)
BEGIN
    DECLARE v_conflict_count INT DEFAULT 0;
    DECLARE v_error_msg VARCHAR(255);
    
    -- Get all ingredients in the batch (flattened one level)
    -- Check for conflicts
    SELECT COUNT(DISTINCT CONCAT(LEAST(dnc.ingredient1_id, dnc.ingredient2_id), 
                                 '-', GREATEST(dnc.ingredient1_id, dnc.ingredient2_id)))
    INTO v_conflict_count
    FROM Product_Batches pb
    JOIN Recipe_Plans rp ON pb.plan_id = rp.plan_id
    JOIN Recipe_Ingredients ri1 ON rp.plan_id = ri1.plan_id
    JOIN Recipe_Ingredients ri2 ON rp.plan_id = ri2.plan_id
    JOIN Ingredients i1 ON ri1.ingredient_id = i1.ingredient_id
    JOIN Ingredients i2 ON ri2.ingredient_id = i2.ingredient_id
    LEFT JOIN Ingredient_Compositions ic1 ON i1.ingredient_id = ic1.parent_ingredient_id
    LEFT JOIN Ingredient_Compositions ic2 ON i2.ingredient_id = ic2.parent_ingredient_id
    JOIN Do_Not_Combine dnc ON (
        (COALESCE(ic1.child_ingredient_id, ri1.ingredient_id) = dnc.ingredient1_id
         AND COALESCE(ic2.child_ingredient_id, ri2.ingredient_id) = dnc.ingredient2_id)
        OR
        (COALESCE(ic1.child_ingredient_id, ri1.ingredient_id) = dnc.ingredient2_id
         AND COALESCE(ic2.child_ingredient_id, ri2.ingredient_id) = dnc.ingredient1_id)
    )
    WHERE pb.batch_number = p_batch_number
      AND ri1.ingredient_id != ri2.ingredient_id;
    
    SET p_conflict_count = v_conflict_count;
    SET p_has_conflict = (v_conflict_count > 0);
    
    IF p_has_conflict THEN
        SET v_error_msg = CONCAT('Health risk detected: ', v_conflict_count, ' incompatible ingredient pair(s) found');
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = v_error_msg;
    END IF;
END//

DELIMITER ;

-- ============================================
-- VIEWS
-- ============================================

-- View 1: Current Active Supplier Formulations
DROP VIEW IF EXISTS v_active_supplier_formulations;
CREATE VIEW v_active_supplier_formulations AS
SELECT 
    f.formulation_id,
    f.supplier_id,
    s.supplier_name,
    f.ingredient_id,
    i.ingredient_name,
    f.name as formulation_name,
    fv.version_id,
    fv.version_no,
    fv.pack_size,
    fv.unit_price,
    fv.effective_from,
    fv.effective_to
FROM Formulations f
JOIN Suppliers s ON f.supplier_id = s.supplier_id
JOIN Ingredients i ON f.ingredient_id = i.ingredient_id
JOIN Formulation_Versions fv ON f.formulation_id = fv.formulation_id
WHERE fv.is_active = TRUE
  AND (fv.effective_to IS NULL OR fv.effective_to >= CURDATE())
  AND fv.effective_from <= CURDATE();

-- View 2: Flattened Product BOM for Labeling
DROP VIEW IF EXISTS v_flattened_product_bom;
CREATE VIEW v_flattened_product_bom AS
SELECT 
    p.product_id,
    p.product_name,
    rp.plan_id,
    rp.version_number,
    COALESCE(ic.child_ingredient_id, ri.ingredient_id) as ingredient_id,
    COALESCE(ci.ingredient_name, i.ingredient_name) as ingredient_name,
    SUM(ri.quantity_required * COALESCE(ic.quantity_required, 1)) as total_quantity_oz
FROM Products p
JOIN Recipe_Plans rp ON p.product_id = rp.product_id
JOIN Recipe_Ingredients ri ON rp.plan_id = ri.plan_id
JOIN Ingredients i ON ri.ingredient_id = i.ingredient_id
LEFT JOIN Ingredient_Compositions ic ON i.ingredient_id = ic.parent_ingredient_id
LEFT JOIN Ingredients ci ON ic.child_ingredient_id = ci.ingredient_id
WHERE rp.is_active = TRUE
GROUP BY p.product_id, p.product_name, rp.plan_id, rp.version_number,
         COALESCE(ic.child_ingredient_id, ri.ingredient_id),
         COALESCE(ci.ingredient_name, i.ingredient_name)
ORDER BY p.product_id, total_quantity_oz DESC;

-- View 3: Health-Risk Rule Violations (Last 30 Days)
DROP VIEW IF EXISTS v_health_risk_violations;
CREATE VIEW v_health_risk_violations AS
SELECT DISTINCT
    pb.batch_number,
    pb.production_date,
    p.product_name,
    dnc.ingredient1_id,
    i1.ingredient_name as ingredient1_name,
    dnc.ingredient2_id,
    i2.ingredient_name as ingredient2_name,
    dnc.reason
FROM Product_Batches pb
JOIN Products p ON pb.product_id = p.product_id
JOIN Recipe_Plans rp ON pb.plan_id = rp.plan_id
JOIN Recipe_Ingredients ri1 ON rp.plan_id = ri1.plan_id
JOIN Recipe_Ingredients ri2 ON rp.plan_id = ri2.plan_id
JOIN Ingredients i1 ON ri1.ingredient_id = i1.ingredient_id
JOIN Ingredients i2 ON ri2.ingredient_id = i2.ingredient_id
LEFT JOIN Ingredient_Compositions ic1 ON i1.ingredient_id = ic1.parent_ingredient_id
LEFT JOIN Ingredient_Compositions ic2 ON i2.ingredient_id = ic2.parent_ingredient_id
JOIN Do_Not_Combine dnc ON (
    (COALESCE(ic1.child_ingredient_id, ri1.ingredient_id) = dnc.ingredient1_id
     AND COALESCE(ic2.child_ingredient_id, ri2.ingredient_id) = dnc.ingredient2_id)
    OR
    (COALESCE(ic1.child_ingredient_id, ri1.ingredient_id) = dnc.ingredient2_id
     AND COALESCE(ic2.child_ingredient_id, ri2.ingredient_id) = dnc.ingredient1_id)
)
WHERE pb.production_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND ri1.ingredient_id != ri2.ingredient_id
ORDER BY pb.production_date DESC;


