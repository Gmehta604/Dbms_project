-- =====================================================================
-- CREATE DATABASE
-- =====================================================================

DROP DATABASE IF EXISTS Meal_Manufacturer;
CREATE DATABASE Meal_Manufacturer;
USE Meal_Manufacturer;


-- =====================================================================
-- 0. DROP TABLES IF THEY EXIST (in correct dependency order)
-- =====================================================================

DROP TABLE IF EXISTS BatchConsumption;
DROP TABLE IF EXISTS ProductBatch;
DROP TABLE IF EXISTS IngredientBatch;
DROP TABLE IF EXISTS FormulationMaterials;
DROP TABLE IF EXISTS Formulation;
DROP TABLE IF EXISTS RecipeIngredient;
DROP TABLE IF EXISTS Recipe;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS DoNotCombine;
DROP TABLE IF EXISTS ingredient;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS AppUser;
DROP TABLE IF EXISTS Supplier;
DROP TABLE IF EXISTS Manufacturer;


-- =====================================================================
-- 1. USER AND ROLE MANAGEMENT
-- =====================================================================

CREATE TABLE Manufacturer (
    manufacturer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE Supplier (
    supplier_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE AppUser (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Manufacturer', 'Supplier', 'Viewer') NOT NULL,
    manufacturer_id VARCHAR(20) NULL,
    supplier_id VARCHAR(20) NULL,
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturer(manufacturer_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    CONSTRAINT chk_user_role CHECK (
        (role = 'Manufacturer' AND manufacturer_id IS NOT NULL AND supplier_id IS NULL) OR
        (role = 'Supplier' AND supplier_id IS NOT NULL AND manufacturer_id IS NULL) OR
        (role = 'Viewer' AND manufacturer_id IS NULL AND supplier_id IS NULL)
    )
);

-- =====================================================================
-- 2. PRODUCT & RECIPE DEFINITIONS
-- =====================================================================

CREATE TABLE Category (
    category_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Ingredient (
    ingredient_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    ingredient_type ENUM('ATOMIC', 'COMPOUND') NOT NULL
);

CREATE TABLE Product (
    product_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id VARCHAR(20) NOT NULL,
    manufacturer_id VARCHAR(20) NOT NULL,
    standard_batch_size INT NOT NULL CHECK (standard_batch_size > 0),
    FOREIGN KEY (category_id) REFERENCES Category(category_id),
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturer(manufacturer_id)
);

CREATE TABLE Recipe (
    recipe_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    creation_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    UNIQUE KEY (product_id, name)
);

CREATE TABLE RecipeIngredient (
    recipe_id INT NOT NULL,
    ingredient_id VARCHAR(20) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    PRIMARY KEY (recipe_id, ingredient_id),
    FOREIGN KEY (recipe_id) REFERENCES Recipe(recipe_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id)
);

-- =====================================================================
-- 3. SUPPLIER FORMULATIONS
-- =====================================================================

CREATE TABLE Formulation (
    formulation_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_id VARCHAR(20) NOT NULL,
    ingredient_id VARCHAR(20) NOT NULL,
    pack_size VARCHAR(50) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    valid_from_date DATE NOT NULL,
    valid_to_date DATE,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id)
);

CREATE TABLE FormulationMaterials (
    formulation_id INT NOT NULL,
    material_ingredient_id VARCHAR(20) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (formulation_id, material_ingredient_id),
    FOREIGN KEY (formulation_id) REFERENCES Formulation(formulation_id),
    FOREIGN KEY (material_ingredient_id) REFERENCES Ingredient(ingredient_id)
);

-- =====================================================================
-- 4. INVENTORY & TRACEABILITY
-- =====================================================================

CREATE TABLE IngredientBatch (
    lot_number VARCHAR(255) PRIMARY KEY,
    ingredient_id VARCHAR(20) NOT NULL,
    supplier_id VARCHAR(20) NOT NULL,
    supplier_batch_id VARCHAR(100) NOT NULL,
    quantity_on_hand DECIMAL(10, 2) NOT NULL,
    per_unit_cost DECIMAL(10, 2) NOT NULL,
    expiration_date DATE NOT NULL,
    intake_date DATE NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    UNIQUE KEY (ingredient_id, supplier_id, supplier_batch_id)
);

CREATE TABLE ProductBatch (
    lot_number VARCHAR(255) PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL,
    manufacturer_id VARCHAR(20) NOT NULL,
    manufacturer_batch_id VARCHAR(100) NOT NULL,
    produced_quantity INT NOT NULL,
    expiration_date DATE NOT NULL,
    production_date DATETIME NOT NULL,
    total_batch_cost DECIMAL(10, 2),
    recipe_id_used INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturer(manufacturer_id),
    FOREIGN KEY (recipe_id_used) REFERENCES Recipe(recipe_id),
    UNIQUE KEY (product_id, manufacturer_id, manufacturer_batch_id)
);

CREATE TABLE BatchConsumption (
    product_lot_number VARCHAR(255) NOT NULL,
    ingredient_lot_number VARCHAR(255) NOT NULL,
    quantity_consumed DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (product_lot_number, ingredient_lot_number),
    FOREIGN KEY (product_lot_number) REFERENCES ProductBatch(lot_number),
    FOREIGN KEY (ingredient_lot_number) REFERENCES IngredientBatch(lot_number)
);

-- =====================================================================
-- 5. GRADUATE FEATURES
-- =====================================================================

CREATE TABLE DoNotCombine (
    ingredient_a_id VARCHAR(20) NOT NULL,
    ingredient_b_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (ingredient_a_id, ingredient_b_id),
    FOREIGN KEY (ingredient_a_id) REFERENCES Ingredient(ingredient_id),
    FOREIGN KEY (ingredient_b_id) REFERENCES Ingredient(ingredient_id),
    CONSTRAINT chk_ingredient_order CHECK (ingredient_a_id < ingredient_b_id)
);

-- ============================================
-- DROP Triggers and Procedures if exists
-- ============================================

DROP TRIGGER IF EXISTS trg_compute_ingredient_lot_number;
DROP TRIGGER IF EXISTS trg_compute_product_lot_number;
DROP TRIGGER IF EXISTS trg_validate_consumption;
DROP TRIGGER IF EXISTS trg_maintain_on_hand_CONSUME;
DROP TRIGGER IF EXISTS trg_maintain_on_hand_ADJUST;
DROP PROCEDURE IF EXISTS Evaluate_Health_Risk;
DROP PROCEDURE IF EXISTS Record_Production_Batch;
DROP PROCEDURE IF EXISTS Trace_Recall;
trg_compute_ingredient_lot_number

-- ============================================
-- Compute Ingredient Lot Trigger
-- ============================================

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

-- ============================================
-- Compute Product Lot Trigger
-- ============================================
//
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
//

-- ============================================
-- Master Consumption Validation Trigger
-- ============================================

//
CREATE TRIGGER trg_validate_consumption
BEFORE INSERT ON BatchConsumption
FOR EACH ROW
BEGIN
    DECLARE v_expiration_date DATE;
    DECLARE v_quantity_on_hand DECIMAL(10, 2);

    SELECT expiration_date, quantity_on_hand 
    INTO v_expiration_date, v_quantity_on_hand
    FROM IngredientBatch
    WHERE lot_number = NEW.ingredient_lot_number;

    IF CURDATE() > v_expiration_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Cannot consume an expired ingredient lot! Lot has expired.';
    END IF;

    IF v_quantity_on_hand < NEW.quantity_consumed THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Not enough quantity on hand. A-vailable: v_quantity_on_hand, Tried to consume: NEW.quantity_consumed';
    END IF;
END;
//

-- ============================================
-- Maintain On-Hand Triggers
-- ============================================
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

-- ============================================
-- Procedures (already DROP IF EXISTS)
-- ============================================
-- Evaluate_Health_Risk

//
CREATE PROCEDURE Evaluate_Health_Risk(IN p_consumption_list JSON)
BEGIN
    DECLARE v_conflict_count INT DEFAULT 0;
    CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Flattened_Atomics (ingredient_id VARCHAR(20) PRIMARY KEY);
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


    INSERT INTO Temp_Affected_Lots (lot_number)
    SELECT lot FROM JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
        lot VARCHAR(255) PATH '$.lot'
    )) AS jt;

    INSERT IGNORE INTO Temp_Flattened_Atomics (ingredient_id)
    SELECT ib.ingredient_id
    FROM IngredientBatch ib
    JOIN Temp_Affected_Lots al ON ib.lot_number = al.lot_number
    JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
    WHERE i.ingredient_type = 'ATOMIC';

    INSERT IGNORE INTO Temp_Flattened_Atomics (ingredient_id)
    SELECT fm.material_ingredient_id
    FROM IngredientBatch ib
    JOIN Temp_Affected_Lots al ON ib.lot_number = al.lot_number
    JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
    JOIN Formulation f ON f.ingredient_id = ib.ingredient_id
        AND f.supplier_id = ib.supplier_id
        AND ib.intake_date BETWEEN f.valid_from_date AND COALESCE(f.valid_to_date, '9999-12-31')
    JOIN FormulationMaterials fm ON fm.formulation_id = f.formulation_id
    WHERE i.ingredient_type = 'COMPOUND';

    INSERT INTO Temp_Flattened_Atomics_2 (ingredient_id)
    SELECT ingredient_id FROM Temp_Flattened_Atomics;

    SELECT COUNT(*) INTO v_conflict_count
    FROM Temp_Flattened_Atomics AS t1
    JOIN DoNotCombine AS dnc ON t1.ingredient_id = dnc.ingredient_a_id
    JOIN Temp_Flattened_Atomics_2 AS t2 ON dnc.ingredient_b_id = t2.ingredient_id;

    SET v_conflict_count = v_conflict_count + (
        SELECT COUNT(*)
        FROM Temp_Flattened_Atomics AS t1
        JOIN DoNotCombine AS dnc ON t1.ingredient_id = dnc.ingredient_b_id
        JOIN Temp_Flattened_Atomics_2 AS t2 ON dnc.ingredient_a_id = t2.ingredient_id
    );

    IF v_conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Health risk detected! Incompatible ingredients found in batch.';
    END IF;
END;
//

-- Record_Production_Batch
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
    DECLARE v_total_cost DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_new_lot_number VARCHAR(255);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    CALL Evaluate_Health_Risk(p_consumption_list);

    SELECT SUM(jt.qty * ib.per_unit_cost) INTO v_total_cost
    FROM JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
        lot VARCHAR(255) PATH '$.lot',
        qty DECIMAL(10,2) PATH '$.qty'
    )) AS jt
    JOIN IngredientBatch ib ON ib.lot_number = jt.lot;

    INSERT INTO ProductBatch
      (product_id, manufacturer_id, manufacturer_batch_id, produced_quantity, production_date, expiration_date, recipe_id_used, total_batch_cost)
    VALUES
      (p_product_id, p_manufacturer_id, p_manufacturer_batch_id, p_produced_quantity, CURDATE(), p_expiration_date, p_recipe_id_used, v_total_cost);

    SET v_new_lot_number = CONCAT(p_product_id,'-',p_manufacturer_id,'-',p_manufacturer_batch_id);

    INSERT INTO BatchConsumption (product_lot_number, ingredient_lot_number, quantity_consumed)
    SELECT v_new_lot_number, jt.lot, jt.qty
    FROM JSON_TABLE(p_consumption_list, '$[*]' COLUMNS (
        lot VARCHAR(255) PATH '$.lot',
        qty DECIMAL(10,2) PATH '$.qty'
    )) AS jt;

    COMMIT;
END;
//

-- Trace_Recall
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
    FROM BatchConsumption bc
    JOIN ProductBatch pb ON bc.product_lot_number = pb.lot_number
    JOIN Product p ON pb.product_id = p.product_id
    WHERE bc.ingredient_lot_number = p_ingredient_lot_number
      AND DATE(pb.production_date) BETWEEN (p_recall_date - INTERVAL 20 DAY) AND p_recall_date;
END;
//

DELIMITER ;