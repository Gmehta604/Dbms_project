-- ============================================
-- SAMPLE DATA INSERTION
-- Meal Manufacturer Database
-- ============================================

USE Meal_Manufacturer;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE Batch_Consumption;
TRUNCATE TABLE Product_Batches;
TRUNCATE TABLE Recipe_Ingredients;
TRUNCATE TABLE Recipe_Plans;
TRUNCATE TABLE Ingredient_Batches;
TRUNCATE TABLE Product_Batches;  
TRUNCATE TABLE Formulation_Versions;
TRUNCATE TABLE Formulations;
TRUNCATE TABLE Supplier_Ingredients;
TRUNCATE TABLE Ingredient_Compositions;
TRUNCATE TABLE Ingredients;
TRUNCATE TABLE Products;
TRUNCATE TABLE Categories;
TRUNCATE TABLE Suppliers;
TRUNCATE TABLE Manufacturers;
TRUNCATE TABLE Users;
TRUNCATE TABLE Do_Not_Combine;

-- ============================================
-- USERS
-- ============================================
INSERT INTO Users (user_id, username, password, role, name, contact_info) VALUES
('MFG001', 'johnsmith', 'password123', 'Manufacturer', 'John Smith', NULL),
('MFG002', 'alicelee', 'password123', 'Manufacturer', 'Alice Lee', NULL),
('SUP020', 'janedoe', 'password123', 'Supplier', 'Jane Doe', NULL),
('SUP021', 'jamesmiller', 'password123', 'Supplier', 'James Miller', NULL),
('VIEW001', 'bobjohnson', 'password123', 'Viewer', 'Bob Johnson', NULL);
-- ============================================
-- MANUFACTURERS
-- ============================================
INSERT INTO Manufacturers (manufacturer_id, user_id, manufacturer_name) VALUES
(1, 'MFG001', 'John Smith Manufacturing'),
(2, 'MFG002', 'Alice Lee Foods');
-- ============================================
-- SUPPLIERS
-- ============================================
INSERT INTO Suppliers (supplier_id, user_id, supplier_name) VALUES
(20, 'SUP020', 'Jane Doe'),
(21, 'SUP021', 'James Miller');

-- ============================================
-- CATEGORIES
-- ============================================
-- Note: category_id is NOT AUTO_INCREMENT, so we insert with explicit IDs
INSERT INTO Categories (category_id, category_name) VALUES
(2, 'Dinners'),
(3, 'Sides');

-- ============================================
-- PRODUCTS
-- ============================================
-- Note: product_id is NOT AUTO_INCREMENT, so we insert with explicit IDs
-- Based on ProductBatch: 100-MFG001 and 101-MFG002, we can infer:
-- Product 100 (Steak Dinner) -> Manufacturer 1 (MFG001/John Smith)
-- Product 101 (Mac & Cheese) -> Manufacturer 2 (MFG002/Alice Lee)
INSERT INTO Products (product_id, product_number, manufacturer_id, category_id, product_name, standard_batch_size, created_date) VALUES
(100, 'P-100', 1, 2, 'Steak Dinner', 100, '2025-01-01'),
(101, 'P-101', 2, 3, 'Mac & Cheese', 300, '2025-01-01');

-- ============================================
-- INGREDIENTS
-- ============================================
-- Note: ingredient_id is NOT AUTO_INCREMENT, so we insert with explicit IDs
INSERT INTO Ingredients (ingredient_id, ingredient_name, ingredient_type, unit_of_measure, description) VALUES
(101, 'Salt', 'Atomic', 'oz', 'Table salt'),
(102, 'Pepper', 'Atomic', 'oz', 'Black pepper'),
(104, 'Sodium Phosphate', 'Atomic', 'oz', 'Food additive'),
(106, 'Beef Steak', 'Atomic', 'oz', 'Beef steak cut'),
(108, 'Pasta', 'Atomic', 'oz', 'Pasta noodles'),
(201, 'Seasoning Blend', 'Compound', 'oz', 'Blend of salt and pepper'),
(301, 'Super Seasoning', 'Compound', 'oz', 'Advanced seasoning blend');

-- ============================================
-- INGREDIENT_COMPOSITIONS
-- ============================================
-- Based on FormulationMaterials: formulation 1 (Seasoning Blend) contains:
-- Salt (101): 6.0 oz
-- Pepper (102): 2.0 oz
-- This represents the composition of the compound ingredient Seasoning Blend (201)

INSERT INTO Ingredient_Compositions (parent_ingredient_id, child_ingredient_id, quantity_required) VALUES
(201, 101, 6.0),  -- Seasoning Blend contains 6.0 oz Salt
(201, 102, 2.0);  -- Seasoning Blend contains 2.0 oz Pepper

-- ============================================
-- SUPPLIER_INGREDIENTS
-- ============================================
-- Jane Doe (supplier 20) supplies: Salt, Pepper, Beef Steak, Pasta, Seasoning Blend
-- James Miller (supplier 21) supplies: Salt (based on IngredientBatch data)

INSERT INTO Supplier_Ingredients (supplier_id, ingredient_id, is_active) VALUES
(20, 101, TRUE),  -- Jane Doe supplies Salt
(20, 102, TRUE),  -- Jane Doe supplies Pepper
(20, 106, TRUE),  -- Jane Doe supplies Beef Steak
(20, 108, TRUE),  -- Jane Doe supplies Pasta
(20, 201, TRUE),  -- Jane Doe supplies Seasoning Blend
(21, 101, TRUE);  -- James Miller supplies Salt

-- ============================================
-- FORMULATIONS
-- ============================================
-- IngredientFormulation: formulation_id=1, ingredient_id=201 (Seasoning Blend), supplier_id=20 (Jane Doe)

INSERT INTO Formulations (formulation_id, supplier_id, ingredient_id, name) VALUES
(1, 20, 201, 'Jane Doe Seasoning Blend');

-- ============================================
-- FORMULATION_VERSIONS
-- ============================================
-- formulation_id=1, version_no=1, effective_start=2025-01-01, effective_end=2025-06-30
-- price_per_pack=20.0, pack_size=8.0

INSERT INTO Formulation_Versions (version_id, formulation_id, version_no, pack_size, unit_price, effective_from, effective_to, is_active) VALUES
(1, 1, 1, 8.0, 20.0, '2025-01-01', '2025-06-30', TRUE);

-- ============================================
-- INGREDIENT_BATCHES
-- ============================================
INSERT INTO Ingredient_Batches (lot_number, ingredient_id, supplier_id, version_id, quantity_on_hand, cost_per_unit, expiration_date, received_date) VALUES
-- Salt batches from Jane Doe (supplier 20)
('101-20-B0001', 101, 20, NULL, 1000, 0.10, '2025-11-15', '2025-08-17'),
('101-20-B0002', 101, 20, NULL, 500, 0.10, '2025-11-01', '2025-08-03'),
('101-20-B0003', 101, 20, NULL, 500, 0.10, '2025-12-15', '2025-09-16'),
-- Salt batch from James Miller (supplier 21)
('101-21-B0001', 101, 21, NULL, 800, 0.08, '2025-10-30', '2025-08-01'),
-- Pepper batch from Jane Doe
('102-20-B0001', 102, 20, NULL, 1200, 0.30, '2025-12-15', '2025-09-16'),
-- Beef Steak batches from Jane Doe
('106-20-B0005', 106, 20, NULL, 3000, 0.50, '2025-12-15', '2025-09-16'),
('106-20-B0006', 106, 20, NULL, 600, 0.50, '2025-12-20', '2025-09-21'),
-- Pasta batches from Jane Doe
('108-20-B0001', 108, 20, NULL, 1000, 0.25, '2025-09-28', '2025-06-30'),
('108-20-B0003', 108, 20, NULL, 6300, 0.25, '2025-12-31', '2025-10-02'),
-- Seasoning Blend batches from Jane Doe
('201-20-B0001', 201, 20, 1, 100, 2.50, '2025-11-30', '2025-09-01'),
('201-20-B0002', 201, 20, 1, 20, 2.50, '2025-12-30', '2025-10-01');

-- ============================================
-- RECIPE_PLANS
-- ============================================
-- Product 100 (Steak Dinner) - Recipe Plan version 1
-- Product 101 (Mac & Cheese) - Recipe Plan version 1

INSERT INTO Recipe_Plans (plan_id, product_id, version_number, created_date, is_active) VALUES
(1, 100, 1, '2025-01-01', TRUE),  -- Steak Dinner recipe
(2, 101, 1, '2025-01-01', TRUE);  -- Mac & Cheese recipe

-- ============================================
-- RECIPE_INGREDIENTS (ProductBOM)
-- ============================================
-- Product 100 (Steak Dinner):
--   ingredient_id=106 (Beef Steak), qty=6.0
--   ingredient_id=201 (Seasoning Blend), qty=0.2

-- Product 101 (Mac & Cheese):
--   ingredient_id=108 (Pasta), qty=7.0
--   ingredient_id=101 (Salt), qty=0.5
--   ingredient_id=102 (Pepper), qty=2.0

INSERT INTO Recipe_Ingredients (plan_id, ingredient_id, quantity_required) VALUES
(1, 106, 6.0),   -- Steak Dinner: Beef Steak
(1, 201, 0.2),   -- Steak Dinner: Seasoning Blend
(2, 108, 7.0),   -- Mac & Cheese: Pasta
(2, 101, 0.5),   -- Mac & Cheese: Salt
(2, 102, 2.0);   -- Mac & Cheese: Pepper

-- ============================================
-- PRODUCT_BATCHES
-- ============================================
INSERT INTO Product_Batches (batch_number, product_id, plan_id, quantity_produced, total_cost, cost_per_unit, production_date, expiration_date) VALUES
('100-MFG001-B0901', 100, 1, 100, 0, 0, '2025-09-26', '2025-11-15'),
('101-MFG002-B0101', 101, 2, 300, 0, 0, '2025-09-10', '2025-10-30');
-- ============================================
-- BATCH_CONSUMPTION (ProductionConsumption)
-- ============================================
INSERT INTO Batch_Consumption (product_batch_number, ingredient_lot_number, quantity_used) VALUES
('100-MFG001-B0901', '106-20-B0006', 600),
('100-MFG001-B0901', '201-20-B0002', 20),
('101-MFG002-B0101', '101-20-B0002', 150),
('101-MFG002-B0101', '108-20-B0003', 2100),
('101-MFG002-B0101', '102-20-B0001', 600);
-- Update ingredient batch quantities after consumption
UPDATE Ingredient_Batches SET quantity_on_hand = quantity_on_hand - 600 WHERE lot_number = '106-20-B0006';
UPDATE Ingredient_Batches SET quantity_on_hand = quantity_on_hand - 20 WHERE lot_number = '201-20-B0002';
UPDATE Ingredient_Batches SET quantity_on_hand = quantity_on_hand - 150 WHERE lot_number = '101-20-B0002';
UPDATE Ingredient_Batches SET quantity_on_hand = quantity_on_hand - 2100 WHERE lot_number = '108-20-B0003';
UPDATE Ingredient_Batches SET quantity_on_hand = quantity_on_hand - 600 WHERE lot_number = '102-20-B0001';
-- Calculate and update product batch costs
UPDATE Product_Batches SET total_cost = 350.0, cost_per_unit = 3.50 WHERE batch_number = '100-MFG001-B0901';
UPDATE Product_Batches SET total_cost = 720.0, cost_per_unit = 2.40 WHERE batch_number = '101-MFG002-B0101';

-- ============================================
-- DO_NOT_COMBINE (ConflictPairs)
-- ============================================
-- Note: Schema has supplier_id, but sample data doesn't specify supplier
-- We'll use supplier_id = 20 (Jane Doe) as default, or could be general (not supplier-specific)
-- Actually, based on requirements, this should be a general list, not supplier-specific
-- But schema requires supplier_id. Let's use a general approach - maybe supplier 20 or create a general entry

-- The conflicts are:
--   ingredient_a=201 (Seasoning Blend) conflicts with ingredient_b=104 (Sodium Phosphate)
--   ingredient_a=106 (Beef Steak) conflicts with ingredient_b=104 (Sodium Phosphate)

-- Since schema requires supplier_id, we'll insert with supplier_id=20 (Jane Doe)
-- If this should be general, the schema might need adjustment

INSERT INTO Do_Not_Combine (supplier_id, ingredient1_id, ingredient2_id, reason, created_date) VALUES
(20, 201, 104, 'Regulatory restriction', '2025-01-01'),  -- Seasoning Blend cannot combine with Sodium Phosphate
(20, 106, 104, 'Regulatory restriction', '2025-01-01');   -- Beef Steak cannot combine with Sodium Phosphate

-- ============================================
-- DATA INSERTION COMPLETE
-- ============================================

-- Re-enable foreign key checks after all inserts are complete
SET FOREIGN_KEY_CHECKS = 1;

