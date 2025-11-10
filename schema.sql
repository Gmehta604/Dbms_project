-- CSC540 Project 1: Inventory Management System
-- Schema file containing tables, constraints, triggers, and procedures
-- Database: MariaDB/MySQL

-- Drop database if exists and create new one
-- Note: Change database name to match your database (csc_540)
-- DROP DATABASE IF EXISTS csc_540;
-- CREATE DATABASE csc_540;
USE csc_540;

-- ============================================================================
-- TABLE DEFINITIONS
-- ============================================================================

-- Users table (base table for all user types)
CREATE TABLE USERS (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('Manufacturer', 'Supplier', 'Viewer') NOT NULL,
    name VARCHAR(100) NOT NULL,
    contact_info VARCHAR(255),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Manufacturers table
CREATE TABLE MANUFACTURERS (
    manufacturer_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    manufacturer_name VARCHAR(100) NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE
);

-- Suppliers table
CREATE TABLE SUPPLIERS (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    supplier_name VARCHAR(100) NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE
);

-- Categories table
CREATE TABLE CATEGORIES (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL
);

-- Products table
CREATE TABLE PRODUCTS (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    manufacturer_id INT NOT NULL,
    category_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    standard_batch_size INT NOT NULL CHECK (standard_batch_size > 0),
    created_date DATE NOT NULL,
    UNIQUE KEY unique_product_manufacturer (product_name, manufacturer_id),
    FOREIGN KEY (manufacturer_id) REFERENCES MANUFACTURERS(manufacturer_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES CATEGORIES(category_id) ON DELETE RESTRICT
);

-- Ingredients table
CREATE TABLE INGREDIENTS (
    ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_name VARCHAR(100) UNIQUE NOT NULL,
    ingredient_type ENUM('Atomic', 'Compound') NOT NULL,
    unit_of_measure VARCHAR(20) DEFAULT 'oz',
    description TEXT
);

-- Ingredient Compositions (one-level nesting only)
CREATE TABLE INGREDIENT_COMPOSITIONS (
    parent_ingredient_id INT NOT NULL,
    child_ingredient_id INT NOT NULL,
    quantity_required DECIMAL(10, 2) NOT NULL CHECK (quantity_required > 0),
    PRIMARY KEY (parent_ingredient_id, child_ingredient_id),
    FOREIGN KEY (parent_ingredient_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (child_ingredient_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE CASCADE,
    CHECK (parent_ingredient_id != child_ingredient_id) -- Prevent self-inclusion
);

-- Supplier Ingredients (which ingredients each supplier can provide)
CREATE TABLE SUPPLIER_INGREDIENTS (
    supplier_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (supplier_id, ingredient_id),
    FOREIGN KEY (supplier_id) REFERENCES SUPPLIERS(supplier_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE CASCADE
);

-- Formulations table
CREATE TABLE FORMULATIONS (
    formulation_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES SUPPLIERS(supplier_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE CASCADE,
    UNIQUE KEY unique_formulation (supplier_id, ingredient_id, name)
);

-- Formulation Versions (with effective dates)
CREATE TABLE FORMULATION_VERSIONS (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    formulation_id INT NOT NULL,
    pack_size DECIMAL(10, 2) NOT NULL CHECK (pack_size > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (formulation_id) REFERENCES FORMULATIONS(formulation_id) ON DELETE CASCADE,
    CHECK (effective_to IS NULL OR effective_to >= effective_from) -- Prevent invalid date ranges
);

-- Ingredient Batches table
CREATE TABLE INGREDIENT_BATCHES (
    ingredient_batch_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_id INT NOT NULL,
    supplier_id INT NOT NULL,
    version_id INT,
    lot_number VARCHAR(100) UNIQUE NOT NULL,
    quantity_on_hand DECIMAL(10, 2) NOT NULL CHECK (quantity_on_hand >= 0),
    cost_per_unit DECIMAL(10, 2) NOT NULL CHECK (cost_per_unit >= 0),
    expiration_date DATE NOT NULL,
    received_date DATE NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES SUPPLIERS(supplier_id) ON DELETE RESTRICT,
    FOREIGN KEY (version_id) REFERENCES FORMULATION_VERSIONS(version_id) ON DELETE SET NULL
);

-- Recipe Plans table (versioned)
CREATE TABLE RECIPE_PLANS (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    version_number INT NOT NULL,
    created_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (product_id) REFERENCES PRODUCTS(product_id) ON DELETE CASCADE,
    UNIQUE KEY unique_plan_version (product_id, version_number)
);

-- Recipe Ingredients table (BOM for products)
CREATE TABLE RECIPE_INGREDIENTS (
    plan_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity_required DECIMAL(10, 2) NOT NULL CHECK (quantity_required > 0),
    PRIMARY KEY (plan_id, ingredient_id),
    FOREIGN KEY (plan_id) REFERENCES RECIPE_PLANS(plan_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE RESTRICT
);

-- Product Batches table
CREATE TABLE PRODUCT_BATCHES (
    product_batch_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    plan_id INT NOT NULL,
    batch_number VARCHAR(100) UNIQUE NOT NULL,
    quantity_produced INT NOT NULL CHECK (quantity_produced > 0),
    total_cost DECIMAL(10, 2) NOT NULL CHECK (total_cost >= 0),
    cost_per_unit DECIMAL(10, 2) NOT NULL CHECK (cost_per_unit >= 0),
    production_date DATE NOT NULL,
    expiration_date DATE,
    FOREIGN KEY (product_id) REFERENCES PRODUCTS(product_id) ON DELETE RESTRICT,
    FOREIGN KEY (plan_id) REFERENCES RECIPE_PLANS(plan_id) ON DELETE RESTRICT
);

-- Batch Consumption table (tracks which ingredient batches were used in product batches)
CREATE TABLE BATCH_CONSUMPTION (
    product_batch_id INT NOT NULL,
    ingredient_batch_id INT NOT NULL,
    quantity_used DECIMAL(10, 2) NOT NULL CHECK (quantity_used > 0),
    PRIMARY KEY (product_batch_id, ingredient_batch_id),
    FOREIGN KEY (product_batch_id) REFERENCES PRODUCT_BATCHES(product_batch_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_batch_id) REFERENCES INGREDIENT_BATCHES(ingredient_batch_id) ON DELETE RESTRICT
);

-- Do Not Combine table (incompatibility rules)
CREATE TABLE DO_NOT_COMBINE (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient1_id INT NOT NULL,
    ingredient2_id INT NOT NULL,
    reason TEXT,
    created_date DATE NOT NULL,
    FOREIGN KEY (ingredient1_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient2_id) REFERENCES INGREDIENTS(ingredient_id) ON DELETE CASCADE,
    CHECK (ingredient1_id != ingredient2_id), -- Prevent self-conflict
    UNIQUE KEY unique_incompatibility (ingredient1_id, ingredient2_id),
    UNIQUE KEY unique_incompatibility_reverse (ingredient2_id, ingredient1_id) -- Ensure bidirectional uniqueness
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_ingredient_batches_expiration ON INGREDIENT_BATCHES(expiration_date);
CREATE INDEX idx_ingredient_batches_lot ON INGREDIENT_BATCHES(lot_number);
CREATE INDEX idx_product_batches_number ON PRODUCT_BATCHES(batch_number);
CREATE INDEX idx_formulation_versions_active ON FORMULATION_VERSIONS(is_active, effective_from, effective_to);
CREATE INDEX idx_recipe_plans_active ON RECIPE_PLANS(is_active, product_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger 1: Compute Ingredient Lot Number on insert
-- Format: <ingredientId>-<supplierId>-<batchId>
DELIMITER //

CREATE TRIGGER trg_compute_ingredient_lot_number
BEFORE INSERT ON INGREDIENT_BATCHES
FOR EACH ROW
BEGIN
    DECLARE batch_counter INT;
    
    -- Generate batch ID (incrementing counter for this ingredient-supplier combination)
    SELECT COALESCE(MAX(CAST(SUBSTRING_INDEX(lot_number, '-', -1) AS UNSIGNED)), 0) + 1
    INTO batch_counter
    FROM INGREDIENT_BATCHES
    WHERE ingredient_id = NEW.ingredient_id 
      AND supplier_id = NEW.supplier_id;
    
    -- Set lot number if not provided
    IF NEW.lot_number IS NULL OR NEW.lot_number = '' THEN
        SET NEW.lot_number = CONCAT(NEW.ingredient_id, '-', NEW.supplier_id, '-B', LPAD(batch_counter, 4, '0'));
    END IF;
    
    -- Validate lot number format
    IF NEW.lot_number NOT REGEXP CONCAT('^', NEW.ingredient_id, '-', NEW.supplier_id, '-B[0-9]+$') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Lot number format must be: <ingredientId>-<supplierId>-B<batchId>';
    END IF;
END//

-- Trigger 2: Prevent Expired Consumption
CREATE TRIGGER trg_prevent_expired_consumption
BEFORE INSERT ON BATCH_CONSUMPTION
FOR EACH ROW
BEGIN
    DECLARE exp_date DATE;
    
    -- Get expiration date of the ingredient batch
    SELECT expiration_date INTO exp_date
    FROM INGREDIENT_BATCHES
    WHERE ingredient_batch_id = NEW.ingredient_batch_id;
    
    -- Check if expired
    IF exp_date IS NOT NULL AND exp_date < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot consume expired ingredient batch';
    END IF;
END//

-- Trigger 3: Maintain On-Hand Inventory
-- Update on-hand quantity when ingredient batches are consumed
CREATE TRIGGER trg_maintain_onhand_consumption
AFTER INSERT ON BATCH_CONSUMPTION
FOR EACH ROW
BEGIN
    UPDATE INGREDIENT_BATCHES
    SET quantity_on_hand = quantity_on_hand - NEW.quantity_used
    WHERE ingredient_batch_id = NEW.ingredient_batch_id;
    
    -- Check if quantity goes negative (shouldn't happen due to validation, but safety check)
    IF (SELECT quantity_on_hand FROM INGREDIENT_BATCHES WHERE ingredient_batch_id = NEW.ingredient_batch_id) < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient quantity on hand';
    END IF;
END//

-- Additional trigger: Validate expiration date on ingredient batch creation (90-day rule)
CREATE TRIGGER trg_validate_ingredient_expiration
BEFORE INSERT ON INGREDIENT_BATCHES
FOR EACH ROW
BEGIN
    IF NEW.expiration_date < DATE_ADD(NEW.received_date, INTERVAL 90 DAY) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Expiration date must be at least 90 days from received date';
    END IF;
END//

-- Additional trigger: Validate product batch number format
CREATE TRIGGER trg_validate_product_batch_number
BEFORE INSERT ON PRODUCT_BATCHES
FOR EACH ROW
BEGIN
    DECLARE mfg_id INT;
    DECLARE prod_id INT;
    
    -- Get manufacturer_id from product
    SELECT manufacturer_id INTO mfg_id
    FROM PRODUCTS
    WHERE product_id = NEW.product_id;
    
    SET prod_id = NEW.product_id;
    
    -- Validate batch number format: <productId>-<manufacturerId>-<batchId>
    IF NEW.batch_number NOT REGEXP CONCAT('^', prod_id, '-', mfg_id, '-B[0-9]+$') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Batch number format must be: <productId>-<manufacturerId>-B<batchId>';
    END IF;
END//

DELIMITER ;

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

DELIMITER //

-- Procedure 1: Record Production Batch
-- Creates a product batch, consumes ingredient lots atomically, computes cost
CREATE PROCEDURE sp_record_production_batch(
    IN p_product_id INT,
    IN p_plan_id INT,
    IN p_quantity_produced INT,
    IN p_production_date DATE,
    IN p_expiration_date DATE,
    OUT p_batch_id INT,
    OUT p_batch_number VARCHAR(100),
    OUT p_total_cost DECIMAL(10, 2),
    OUT p_cost_per_unit DECIMAL(10, 2),
    OUT p_status VARCHAR(100),
    OUT p_message TEXT
)
proc_label: BEGIN
    DECLARE v_manufacturer_id INT;
    DECLARE v_standard_batch_size INT;
    DECLARE v_batch_counter INT;
    DECLARE v_total_cost DECIMAL(10, 2) DEFAULT 0;
    DECLARE v_ingredient_id INT;
    DECLARE v_required_qty DECIMAL(10, 2);
    DECLARE v_ingredient_batch_id INT;
    DECLARE v_available_qty DECIMAL(10, 2);
    DECLARE v_cost DECIMAL(10, 2);
    DECLARE v_quantity_used DECIMAL(10, 2);
    DECLARE done INT DEFAULT FALSE;
    DECLARE temp_batch_id INT;
    
    -- Cursor for recipe ingredients
    DECLARE recipe_cursor CURSOR FOR
        SELECT ingredient_id, quantity_required
        FROM RECIPE_INGREDIENTS
        WHERE plan_id = p_plan_id;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR';
        GET DIAGNOSTICS CONDITION 1
            p_message = MESSAGE_TEXT;
    END;
    
    START TRANSACTION;
    
    -- Validate product exists and get manufacturer
    SELECT manufacturer_id, standard_batch_size
    INTO v_manufacturer_id, v_standard_batch_size
    FROM PRODUCTS
    WHERE product_id = p_product_id;
    
    IF v_manufacturer_id IS NULL THEN
        SET p_status = 'ERROR';
        SET p_message = 'Product not found';
        ROLLBACK;
        LEAVE proc_label;
    END IF;
    
    -- Validate quantity is multiple of standard batch size
    IF p_quantity_produced % v_standard_batch_size != 0 THEN
        SET p_status = 'ERROR';
        SET p_message = CONCAT('Quantity must be a multiple of standard batch size: ', v_standard_batch_size);
        ROLLBACK;
        LEAVE proc_label;
    END IF;
    
    -- Generate batch number
    SELECT COALESCE(MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(batch_number, '-', -1), 'B', -1) AS UNSIGNED)), 0) + 1
    INTO v_batch_counter
    FROM PRODUCT_BATCHES
    WHERE product_id = p_product_id;
    
    SET p_batch_number = CONCAT(p_product_id, '-', v_manufacturer_id, '-B', LPAD(v_batch_counter, 4, '0'));
    
    -- Create temporary table to store consumption records
    CREATE TEMPORARY TABLE IF NOT EXISTS temp_consumption (
        ingredient_batch_id INT,
        quantity_used DECIMAL(10, 2),
        cost DECIMAL(10, 2)
    );
    
    -- Process each ingredient in recipe
    OPEN recipe_cursor;
    recipe_loop: LOOP
        FETCH recipe_cursor INTO v_ingredient_id, v_required_qty;
        IF done THEN
            LEAVE recipe_loop;
        END IF;
        
        -- Calculate total required quantity for this batch
        SET v_required_qty = v_required_qty * p_quantity_produced;
        
        -- Check if sufficient quantity exists (FEFO: First Expired First Out)
        -- This is a simplified version - full FEFO would select multiple batches
        SELECT ingredient_batch_id, quantity_on_hand, cost_per_unit
        INTO v_ingredient_batch_id, v_available_qty, v_cost
        FROM INGREDIENT_BATCHES
        WHERE ingredient_id = v_ingredient_id
          AND quantity_on_hand >= v_required_qty
          AND expiration_date >= CURDATE()
        ORDER BY expiration_date ASC
        LIMIT 1;
        
        IF v_ingredient_batch_id IS NULL THEN
            SET p_status = 'ERROR';
            SET p_message = CONCAT('Insufficient quantity or expired batches for ingredient ID: ', v_ingredient_id);
            CLOSE recipe_cursor;
            DROP TEMPORARY TABLE IF EXISTS temp_consumption;
            ROLLBACK;
            LEAVE proc_label;
        END IF;
        
        -- Store consumption record temporarily
        INSERT INTO temp_consumption (ingredient_batch_id, quantity_used, cost)
        VALUES (v_ingredient_batch_id, v_required_qty, v_cost);
        
        -- Calculate cost
        SET v_total_cost = v_total_cost + (v_required_qty * v_cost);
    END LOOP;
    CLOSE recipe_cursor;
    
    -- Calculate per-unit cost
    SET p_total_cost = v_total_cost;
    SET p_cost_per_unit = v_total_cost / p_quantity_produced;
    
    -- Insert product batch
    INSERT INTO PRODUCT_BATCHES (
        product_id, plan_id, batch_number, quantity_produced,
        total_cost, cost_per_unit, production_date, expiration_date
    ) VALUES (
        p_product_id, p_plan_id, p_batch_number, p_quantity_produced,
        p_total_cost, p_cost_per_unit, p_production_date, p_expiration_date
    );
    
    SET p_batch_id = LAST_INSERT_ID();
    
    -- Insert batch consumption records
    INSERT INTO BATCH_CONSUMPTION (product_batch_id, ingredient_batch_id, quantity_used)
    SELECT p_batch_id, ingredient_batch_id, quantity_used
    FROM temp_consumption;
    
    -- Drop temporary table
    DROP TEMPORARY TABLE IF EXISTS temp_consumption;
    
    -- Evaluate health risk (check for do-not-combine conflicts)
    CALL sp_evaluate_health_risk(p_batch_id, @health_status, @health_message);
    
    IF @health_status = 'CONFLICT' THEN
        SET p_status = 'WARNING';
        SET p_message = CONCAT('Batch created with warnings: ', @health_message);
    ELSE
        SET p_status = 'SUCCESS';
        SET p_message = 'Production batch recorded successfully';
    END IF;
    
    COMMIT;
END proc_label//

-- Procedure 2: Trace Recall
-- Given ingredient ID or lot number, find affected product batches within time window
CREATE PROCEDURE sp_trace_recall(
    IN p_ingredient_id INT,
    IN p_lot_number VARCHAR(100),
    IN p_days_window INT,
    OUT p_affected_batches TEXT
)
BEGIN
    DECLARE v_start_date DATE;
    DECLARE v_affected_count INT DEFAULT 0;
    
    -- Calculate start date based on window
    SET v_start_date = DATE_SUB(CURDATE(), INTERVAL p_days_window DAY);
    
    -- Build list of affected product batches
    IF p_lot_number IS NOT NULL AND p_lot_number != '' THEN
        -- Trace by specific lot number
        SELECT GROUP_CONCAT(DISTINCT pb.batch_number ORDER BY pb.batch_number SEPARATOR ', ')
        INTO p_affected_batches
        FROM PRODUCT_BATCHES pb
        INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
        INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
        WHERE ib.lot_number = p_lot_number
          AND pb.production_date >= v_start_date;
    ELSEIF p_ingredient_id IS NOT NULL THEN
        -- Trace by ingredient ID (including compound ingredients - one level)
        SELECT GROUP_CONCAT(DISTINCT pb.batch_number ORDER BY pb.batch_number SEPARATOR ', ')
        INTO p_affected_batches
        FROM PRODUCT_BATCHES pb
        INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
        INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
        WHERE (ib.ingredient_id = p_ingredient_id
           OR ib.ingredient_id IN (
               SELECT parent_ingredient_id 
               FROM INGREDIENT_COMPOSITIONS 
               WHERE child_ingredient_id = p_ingredient_id
           ))
          AND pb.production_date >= v_start_date;
    ELSE
        SET p_affected_batches = 'Invalid parameters: provide either ingredient_id or lot_number';
    END IF;
    
    IF p_affected_batches IS NULL THEN
        SET p_affected_batches = 'No affected batches found';
    END IF;
END//

-- Procedure 3: Evaluate Health Risk
-- Check if a product batch contains any do-not-combine ingredient pairs
CREATE PROCEDURE sp_evaluate_health_risk(
    IN p_product_batch_id INT,
    OUT p_status VARCHAR(20),
    OUT p_message TEXT
)
BEGIN
    DECLARE conflict_count INT DEFAULT 0;
    DECLARE conflict_list TEXT;
    
    -- Find all ingredients used in this product batch (flattened one level)
    -- Check for conflicts in do-not-combine list
    SELECT COUNT(*), GROUP_CONCAT(
        CONCAT('(', dnc.ingredient1_id, ',', dnc.ingredient2_id, ')') 
        SEPARATOR ', '
    )
    INTO conflict_count, conflict_list
    FROM DO_NOT_COMBINE dnc
    WHERE EXISTS (
        -- Check if ingredient1 is in the batch
        SELECT 1
        FROM BATCH_CONSUMPTION bc1
        INNER JOIN INGREDIENT_BATCHES ib1 ON bc1.ingredient_batch_id = ib1.ingredient_batch_id
        WHERE bc1.product_batch_id = p_product_batch_id
          AND (ib1.ingredient_id = dnc.ingredient1_id
           OR ib1.ingredient_id IN (
               SELECT parent_ingredient_id 
               FROM INGREDIENT_COMPOSITIONS 
               WHERE child_ingredient_id = dnc.ingredient1_id
           ))
    )
    AND EXISTS (
        -- Check if ingredient2 is in the batch
        SELECT 1
        FROM BATCH_CONSUMPTION bc2
        INNER JOIN INGREDIENT_BATCHES ib2 ON bc2.ingredient_batch_id = ib2.ingredient_batch_id
        WHERE bc2.product_batch_id = p_product_batch_id
          AND (ib2.ingredient_id = dnc.ingredient2_id
           OR ib2.ingredient_id IN (
               SELECT parent_ingredient_id 
               FROM INGREDIENT_COMPOSITIONS 
               WHERE child_ingredient_id = dnc.ingredient2_id
           ))
    );
    
    IF conflict_count > 0 THEN
        SET p_status = 'CONFLICT';
        SET p_message = CONCAT('Found ', conflict_count, ' incompatible ingredient pair(s): ', conflict_list);
    ELSE
        SET p_status = 'SAFE';
        SET p_message = 'No incompatible ingredient pairs detected';
    END IF;
END//

DELIMITER ;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View 1: Current Active Supplier Formulations
CREATE VIEW vw_active_formulations AS
SELECT 
    f.formulation_id,
    s.supplier_name,
    i.ingredient_name,
    f.name AS formulation_name,
    fv.version_id,
    fv.pack_size,
    fv.unit_price,
    fv.effective_from,
    fv.effective_to,
    fv.is_active
FROM FORMULATIONS f
INNER JOIN SUPPLIERS s ON f.supplier_id = s.supplier_id
INNER JOIN INGREDIENTS i ON f.ingredient_id = i.ingredient_id
INNER JOIN FORMULATION_VERSIONS fv ON f.formulation_id = fv.formulation_id
WHERE fv.is_active = TRUE
  AND (fv.effective_to IS NULL OR fv.effective_to >= CURDATE())
  AND fv.effective_from <= CURDATE()
ORDER BY s.supplier_name, i.ingredient_name, fv.effective_from DESC;

-- View 2: Flattened Product BOM for Labeling
-- Shows all ingredients (including nested materials) for a product, ordered by quantity
CREATE VIEW vw_flattened_product_bom AS
SELECT 
    p.product_id,
    p.product_name,
    rp.plan_id,
    rp.version_number,
    -- Direct ingredient
    CASE 
        WHEN ic.parent_ingredient_id IS NULL THEN ri.ingredient_id
        ELSE ic.child_ingredient_id
    END AS final_ingredient_id,
    CASE 
        WHEN ic.parent_ingredient_id IS NULL THEN i.ingredient_name
        ELSE child_i.ingredient_name
    END AS final_ingredient_name,
    -- Calculate total quantity contribution (handling compound ingredients)
    CASE 
        WHEN ic.parent_ingredient_id IS NULL THEN ri.quantity_required
        ELSE ri.quantity_required * ic.quantity_required
    END AS total_quantity_contribution
FROM PRODUCTS p
INNER JOIN RECIPE_PLANS rp ON p.product_id = rp.product_id AND rp.is_active = TRUE
INNER JOIN RECIPE_INGREDIENTS ri ON rp.plan_id = ri.plan_id
INNER JOIN INGREDIENTS i ON ri.ingredient_id = i.ingredient_id
LEFT JOIN INGREDIENT_COMPOSITIONS ic ON i.ingredient_id = ic.parent_ingredient_id
LEFT JOIN INGREDIENTS child_i ON ic.child_ingredient_id = child_i.ingredient_id
ORDER BY p.product_id, rp.plan_id, total_quantity_contribution DESC;

-- View 3: Health-Risk Rule Violations (last 30 days)
CREATE VIEW vw_health_risk_violations AS
SELECT 
    pb.product_batch_id,
    pb.batch_number,
    p.product_name,
    pb.production_date,
    dnc.ingredient1_id,
    i1.ingredient_name AS ingredient1_name,
    dnc.ingredient2_id,
    i2.ingredient_name AS ingredient2_name,
    dnc.reason,
    dnc.created_date AS rule_created_date
FROM PRODUCT_BATCHES pb
INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
INNER JOIN BATCH_CONSUMPTION bc1 ON pb.product_batch_id = bc1.product_batch_id
INNER JOIN INGREDIENT_BATCHES ib1 ON bc1.ingredient_batch_id = ib1.ingredient_batch_id
INNER JOIN BATCH_CONSUMPTION bc2 ON pb.product_batch_id = bc2.product_batch_id
INNER JOIN INGREDIENT_BATCHES ib2 ON bc2.ingredient_batch_id = ib2.ingredient_batch_id
INNER JOIN DO_NOT_COMBINE dnc ON (
    (ib1.ingredient_id = dnc.ingredient1_id OR ib1.ingredient_id IN (
        SELECT parent_ingredient_id FROM INGREDIENT_COMPOSITIONS WHERE child_ingredient_id = dnc.ingredient1_id
    ))
    AND (ib2.ingredient_id = dnc.ingredient2_id OR ib2.ingredient_id IN (
        SELECT parent_ingredient_id FROM INGREDIENT_COMPOSITIONS WHERE child_ingredient_id = dnc.ingredient2_id
    ))
)
INNER JOIN INGREDIENTS i1 ON dnc.ingredient1_id = i1.ingredient_id
INNER JOIN INGREDIENTS i2 ON dnc.ingredient2_id = i2.ingredient_id
WHERE pb.production_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND bc1.ingredient_batch_id != bc2.ingredient_batch_id
GROUP BY pb.product_batch_id, dnc.ingredient1_id, dnc.ingredient2_id
ORDER BY pb.production_date DESC;

-- ============================================================================
-- REQUIRED QUERIES
-- ============================================================================

-- Query 1: List the ingredients and the lot number of the last batch of product type 
--          Steak Dinner (100) made by manufacturer MFG001
-- Note: Assuming product_id 100 is Steak Dinner and manufacturer_id 1 is MFG001
-- This will be parameterized in the application

-- Query 2: For manufacturer MFG002, list all the suppliers that they have purchased from 
--          and the total amount of money they have spent with that supplier
-- Note: Assuming manufacturer_id 2 is MFG002

-- Query 3: For product with lot number 100-MFG001-B0901, find the unit cost for that product

-- Query 4: Based on the ingredients currently in product lot number 100-MFG001-B0901, 
--          what are all ingredients that cannot be included (i.e. that are in conflict with the current ingredient list)

-- Query 5: Which manufacturers have supplier James Miller (21) NOT supplied to?

-- These queries will be implemented as stored procedures or views for easy access
-- See queries.sql file for implementation
