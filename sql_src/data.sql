-- =====================================================================
-- POPULATE.SQL
-- This file contains all the sample data from the handout,
-- "marshalled" to fit the schema we designed.
-- This file MUST be run *after* schema.sql and procedures_triggers.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. `Category`
-- ---------------------------------------------------------------------
INSERT INTO Category (category_id, name) VALUES
('2', 'Dinners'),
('3', 'Sides');

-- ---------------------------------------------------------------------
-- 2. `Manufacturer`
-- Data inferred from their 'User' table
-- ---------------------------------------------------------------------
INSERT INTO Manufacturer (manufacturer_id, name) VALUES
('MFG001', 'John Smith (Manufacturer)'),
('MFG002', 'Alice Lee (Manufacturer)');

-- ---------------------------------------------------------------------
-- 3. `Supplier`
-- Data from their 'Supplier' table.
-- ---------------------------------------------------------------------
INSERT INTO Supplier (supplier_id, name) VALUES
('20', 'Jane Doe'),
('21', 'James Miller');

-- ---------------------------------------------------------------------
-- 4. `Ingredient`
-- Data from their 'Ingredient' table.
-- ---------------------------------------------------------------------
INSERT INTO Ingredient (ingredient_id, name, ingredient_type) VALUES
('101', 'Salt', 'ATOMIC'),
('102', 'Pepper', 'ATOMIC'),
('104', 'Sodium Phosphate', 'ATOMIC'),
('106', 'Beef Steak', 'ATOMIC'),
('108', 'Pasta', 'ATOMIC'),
('201', 'Seasoning Blend', 'COMPOUND'),
('301', 'Super Seasoning', 'COMPOUND');

-- ---------------------------------------------------------------------
-- 5. `AppUser`
-- Data mapped from their 'User' table into our schema.
-- Passwords are all 'password123' (in a real system, these would be hashed)
-- ---------------------------------------------------------------------
INSERT INTO AppUser (username, password_hash, role, manufacturer_id, supplier_id) VALUES
('jsmith', 'password123', 'Manufacturer', 'MFG001', NULL),
('alee', 'password123', 'Manufacturer', 'MFG002', NULL),
('jdoe', 'password123', 'Supplier', NULL, '20'),
('jmiller', 'password123', 'Supplier', NULL, '21'),
('bjohnson', 'password123', 'Viewer', NULL, NULL);

-- ---------------------------------------------------------------------
-- 6. `Product`
-- Data mapped from their 'Product' table.
-- We must *invent* the 'manufacturer_id' to match our schema.
-- ---------------------------------------------------------------------
INSERT INTO Product (product_id, name, category_id, manufacturer_id, standard_batch_size) VALUES
('100', 'Steak Dinner', '2', 'MFG001', 100),
('101', 'Mac & Cheese', '3', 'MFG002', 300);

-- ---------------------------------------------------------------------
-- 7. `Recipe`
-- Mapped from their 'ProductBOM' table. We must *invent*
-- a 'Recipe' (version) to be the "parent" of the BOM items.
-- ---------------------------------------------------------------------
INSERT INTO Recipe (recipe_id, product_id, name, creation_date) VALUES
(1, '100', 'v1-Steak-Dinner', '2025-01-01'),
(2, '101', 'v1-Mac-Cheese', '2025-01-01');

-- ---------------------------------------------------------------------
-- 8. `RecipeIngredient`
-- Mapped from their 'ProductBOM' table.
-- We link to the 'recipe_id' we just invented.
-- ---------------------------------------------------------------------
INSERT INTO RecipeIngredient (recipe_id, ingredient_id, quantity, unit_of_measure) VALUES
-- Recipe 1 (Steak Dinner)
(1, '106', 6.0, 'oz'), -- oz is an assumption
(1, '201', 0.2, 'oz'),
-- Recipe 2 (Mac & Cheese)
(2, '108', 7.0, 'oz'),
(2, '101', 0.5, 'oz'),
(2, '102', 2.0, 'oz');

-- ---------------------------------------------------------------------
-- 9. `Formulation`
-- Mapped from their 'IngredientFormulation' table.
-- We'll manually set the PK (formulation_id) to 1.
-- ---------------------------------------------------------------------
INSERT INTO Formulation (formulation_id, ingredient_id, supplier_id, valid_from_date, valid_to_date, unit_price, pack_size) VALUES
(1, '201', '20', '2025-06-01', '2025-11-30', 20.0, '8.0 oz'); -- Made pack_size a string

-- ---------------------------------------------------------------------
-- 10. `FormulationMaterials`
-- Mapped from their 'FormulationMaterials' table.
-- ---------------------------------------------------------------------
INSERT INTO FormulationMaterials (formulation_id, material_ingredient_id, quantity) VALUES
(1, '101', 6.0),
(1, '102', 2.0);

-- ---------------------------------------------------------------------
-- 11. `IngredientBatch`
-- Mapped from their 'IngredientBatch' table.
-- CRITICAL: We do *NOT* insert 'lot_number'. We insert the "parts"
-- and let our trigger 'trg_compute_ingredient_lot_number' build the key.
-- We must *invent* 'intake_date' for the 90-day rule.
-- ---------------------------------------------------------------------
INSERT INTO IngredientBatch 
  (ingredient_id, supplier_id, supplier_batch_id, quantity_on_hand, per_unit_cost, expiration_date, intake_date) 
VALUES
-- Lot Number: 101-20-B0001
('101', '20', 'B0001', 1000, 0.1, '2025-11-15', '2025-09-01'),
-- Lot Number: 101-21-B0001
('101', '21', 'B0001', 800, 0.08, '2025-10-30', '2025-09-01'),
-- Lot Number: 101-20-B0002
('101', '20', 'B0002', 500, 0.1, '2025-11-01', '2025-09-01'),
-- Lot Number: 101-20-B0003
('101', '20', 'B0003', 500, 0.1, '2025-12-15', '2025-09-01'),
-- Lot Number: 102-20-B0001
('102', '20', 'B0001', 1200, 0.3, '2025-12-15', '2025-09-01'),
-- Lot Number: 106-20-B0005
('106', '20', 'B0005', 3000, 0.5, '2025-12-15', '2025-09-01'),
-- Lot Number: 106-20-B0006
('106', '20', 'B0006', 600, 0.5, '2025-12-20', '2025-09-01'),
-- Lot Number: 108-20-B0001
('108', '20', 'B0001', 1000, 0.25, '2025-09-28', '2025-09-01'),
-- Lot Number: 108-20-B0003
('108', '20', 'B0003', 6300, 0.25, '2025-12-31', '2025-09-01'),
-- Lot Number: 201-20-B0001
('201', '20', 'B0001', 100, 2.5, '2025-11-30', '2025-09-01'),
-- Lot Number: 201-20-B0002
('201', '20', 'B0002', 20, 2.5, '2025-12-30', '2025-09-01');

-- ---------------------------------------------------------------------
-- 12. `ProductBatch`
-- Mapped from their 'ProductBatch' table.
-- CRITICAL: We let our trigger build the 'lot_number' PK.
-- We must *invent* 'recipe_id_used' and 'total_batch_cost'.
-- ---------------------------------------------------------------------
INSERT INTO ProductBatch
  (product_id, manufacturer_id, manufacturer_batch_id, produced_quantity, production_date, expiration_date, recipe_id_used, total_batch_cost)
VALUES
-- Lot Number: 100-MFG001-B0901
('100', 'MFG001', 'B0901', 100, '2025-09-26 00:00:00', '2025-11-15', 1, 350.00), -- Cost = (600*0.5) + (20*2.5) = 300 + 50 = 350.00
-- Lot Number: 101-MFG002-B0101
('101', 'MFG002', 'B0101', 300, '2025-09-10 00:00:00', '2025-10-30', 2, 720.00); -- Cost = (150*0.1) + (2100*0.25) + (600*0.3) = 15 + 525 + 180 = 720.00

-- ---------------------------------------------------------------------
-- 13. `BatchConsumption`
-- Mapped from their 'ProductionConsumption' table.
-- We must use the *full computed lot numbers* that our triggers created.
-- ---------------------------------------------------------------------
INSERT INTO BatchConsumption (product_lot_number, ingredient_lot_number, quantity_consumed) VALUES
('100-MFG001-B0901', '106-20-B0006', 600),
('100-MFG001-B0901', '201-20-B0002', 20),
('101-MFG002-B0101', '101-20-B0002', 150),
('101-MFG002-B0101', '108-20-B0003', 2100),
('101-MFG002-B0101', '102-20-B0001', 600);

-- ---------------------------------------------------------------------
-- 14. `DoNotCombine`
-- Mapped from their 'ConflictPairs' table.
-- ---------------------------------------------------------------------
INSERT INTO DoNotCombine (ingredient_a_id, ingredient_b_id) VALUES
('104', '106'); -- We assume 104 < 106 for our CHECK constraint.