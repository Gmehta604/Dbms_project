-- CSC540 Project 1: Inventory Management System
-- Data population file with sample data
-- Database: MariaDB/MySQL

USE csc_540;

-- ============================================================================
-- SAMPLE DATA POPULATION
-- ============================================================================

-- Insert Users
INSERT INTO USERS (username, password, role, name, contact_info) VALUES
-- Manufacturers
('mfg001_user', 'password123', 'Manufacturer', 'John Smith', 'john.smith@mfg001.com'),
('mfg002_user', 'password123', 'Manufacturer', 'Jane Doe', 'jane.doe@mfg002.com'),
('mfg003_user', 'password123', 'Manufacturer', 'Bob Johnson', 'bob.johnson@mfg003.com'),
-- Suppliers
('supplier21_user', 'password123', 'Supplier', 'James Miller', 'james.miller@supplier21.com'),
('supplier22_user', 'password123', 'Supplier', 'Sarah Williams', 'sarah.williams@supplier22.com'),
('supplier23_user', 'password123', 'Supplier', 'Mike Brown', 'mike.brown@supplier23.com'),
-- Viewers
('viewer1', 'password123', 'Viewer', 'Alice Green', 'alice.green@viewer.com'),
('viewer2', 'password123', 'Viewer', 'Tom White', 'tom.white@viewer.com');

-- Insert Manufacturers
INSERT INTO MANUFACTURERS (user_id, manufacturer_name) VALUES
(1, 'MFG001'),
(2, 'MFG002'),
(3, 'MFG003');

-- Insert Suppliers
-- Note: Setting specific IDs to match query requirements (supplier_id = 21 for James Miller)
SET FOREIGN_KEY_CHECKS = 0;
INSERT INTO SUPPLIERS (supplier_id, user_id, supplier_name) VALUES
(21, 4, 'James Miller'),
(22, 5, 'Sarah Williams'),
(23, 6, 'Mike Brown');
SET FOREIGN_KEY_CHECKS = 1;

-- Insert Categories
INSERT INTO CATEGORIES (category_name) VALUES
('Dinners'),
('Sides'),
('Desserts');

-- Insert Products
-- Note: We'll set specific IDs to match query requirements
-- MFG001 products
SET FOREIGN_KEY_CHECKS = 0;
INSERT INTO PRODUCTS (product_id, manufacturer_id, category_id, product_name, standard_batch_size, created_date) VALUES
(100, 1, 1, 'Steak Dinner', 500, '2024-01-15'),
(2, 1, 2, 'Mac & Cheese', 300, '2024-01-20'),
(3, 1, 3, 'Chocolate Lava Cake', 200, '2024-02-01');
SET FOREIGN_KEY_CHECKS = 1;

-- MFG002 products
INSERT INTO PRODUCTS (manufacturer_id, category_id, product_name, standard_batch_size, created_date) VALUES
(2, 1, 'Chicken Dinner', 500, '2024-01-10'),
(2, 2, 'Mashed Potatoes', 400, '2024-01-25');

-- MFG003 products
INSERT INTO PRODUCTS (manufacturer_id, category_id, product_name, standard_batch_size, created_date) VALUES
(3, 1, 'Fish Dinner', 450, '2024-02-05');

-- Insert Ingredients (Atomic)
INSERT INTO INGREDIENTS (ingredient_name, ingredient_type, unit_of_measure, description) VALUES
-- Atomic ingredients
('Beef Steak', 'Atomic', 'oz', 'Premium beef steak'),
('Salt', 'Atomic', 'oz', 'Table salt'),
('Pepper', 'Atomic', 'oz', 'Black pepper'),
('Garlic Powder', 'Atomic', 'oz', 'Dried garlic powder'),
('Sugar', 'Atomic', 'oz', 'Granulated sugar'),
('Flour', 'Atomic', 'oz', 'All-purpose flour'),
('Butter', 'Atomic', 'oz', 'Unsalted butter'),
('Milk', 'Atomic', 'oz', 'Whole milk'),
('Chicken Breast', 'Atomic', 'oz', 'Boneless chicken breast'),
('Potatoes', 'Atomic', 'oz', 'Russet potatoes'),
('Brown Gravy', 'Atomic', 'oz', 'Prepared brown gravy'),
('Herb Butter', 'Atomic', 'oz', 'Butter with herbs'),
('Macaroni', 'Atomic', 'oz', 'Elbow macaroni'),
('Cheddar Cheese', 'Atomic', 'oz', 'Shredded cheddar cheese'),
('Chocolate', 'Atomic', 'oz', 'Dark chocolate'),
('Eggs', 'Atomic', 'oz', 'Large eggs'),
('Vanilla Extract', 'Atomic', 'oz', 'Pure vanilla extract'),
('Fish Fillet', 'Atomic', 'oz', 'White fish fillet'),
('Lemon', 'Atomic', 'oz', 'Fresh lemon');

-- Insert Ingredients (Compound)
INSERT INTO INGREDIENTS (ingredient_name, ingredient_type, unit_of_measure, description) VALUES
('Seasoning Blend', 'Compound', 'oz', 'Mixed seasoning blend'),
('Tomato Sauce', 'Compound', 'oz', 'Prepared tomato sauce');

-- Insert Ingredient Compositions (one-level nesting only)
-- Seasoning Blend = Salt + Pepper + Garlic Powder
INSERT INTO INGREDIENT_COMPOSITIONS (parent_ingredient_id, child_ingredient_id, quantity_required) VALUES
(20, 2, 0.5),  -- Seasoning Blend contains 0.5 oz Salt
(20, 3, 0.3),  -- Seasoning Blend contains 0.3 oz Pepper
(20, 4, 0.2);  -- Seasoning Blend contains 0.2 oz Garlic Powder

-- Tomato Sauce = Salt + Sugar + Flour (simplified)
INSERT INTO INGREDIENT_COMPOSITIONS (parent_ingredient_id, child_ingredient_id, quantity_required) VALUES
(21, 2, 0.1),  -- Tomato Sauce contains 0.1 oz Salt
(21, 5, 0.2),  -- Tomato Sauce contains 0.2 oz Sugar
(21, 6, 0.3);  -- Tomato Sauce contains 0.3 oz Flour

-- Insert Supplier Ingredients (which ingredients each supplier can provide)
-- James Miller (supplier_id = 21) supplies:
INSERT INTO SUPPLIER_INGREDIENTS (supplier_id, ingredient_id, is_active) VALUES
(21, 1, TRUE),  -- Beef Steak
(21, 2, TRUE),  -- Salt
(21, 3, TRUE),  -- Pepper
(21, 4, TRUE),  -- Garlic Powder
(21, 20, TRUE), -- Seasoning Blend
(21, 11, TRUE), -- Brown Gravy
(21, 12, TRUE); -- Herb Butter

-- Sarah Williams (supplier_id = 22) supplies:
INSERT INTO SUPPLIER_INGREDIENTS (supplier_id, ingredient_id, is_active) VALUES
(22, 9, TRUE),  -- Chicken Breast
(22, 10, TRUE), -- Potatoes
(22, 13, TRUE), -- Macaroni
(22, 14, TRUE), -- Cheddar Cheese
(22, 6, TRUE),  -- Flour
(22, 7, TRUE),  -- Butter
(22, 8, TRUE);  -- Milk

-- Mike Brown (supplier_id = 23) supplies:
INSERT INTO SUPPLIER_INGREDIENTS (supplier_id, ingredient_id, is_active) VALUES
(23, 15, TRUE), -- Chocolate
(23, 16, TRUE), -- Eggs
(23, 17, TRUE), -- Vanilla Extract
(23, 5, TRUE),  -- Sugar
(23, 18, TRUE), -- Fish Fillet
(23, 19, TRUE); -- Lemon

-- Insert Formulations
-- James Miller's formulations
INSERT INTO FORMULATIONS (supplier_id, ingredient_id, name) VALUES
(21, 20, 'Standard Seasoning Blend'),
(21, 11, 'Classic Brown Gravy'),
(21, 12, 'Herb Butter Mix');

-- Sarah Williams' formulations
INSERT INTO FORMULATIONS (supplier_id, ingredient_id, name) VALUES
(22, 13, 'Premium Macaroni'),
(22, 14, 'Sharp Cheddar Cheese');

-- Insert Formulation Versions
-- James Miller - Seasoning Blend
INSERT INTO FORMULATION_VERSIONS (formulation_id, pack_size, unit_price, effective_from, effective_to, is_active) VALUES
(1, 10.0, 5.50, '2024-01-01', NULL, TRUE),  -- 10 oz pack, $5.50 per pack
(1, 10.0, 5.75, '2024-03-01', NULL, FALSE); -- Updated price (not yet active)

-- James Miller - Brown Gravy
INSERT INTO FORMULATION_VERSIONS (formulation_id, pack_size, unit_price, effective_from, effective_to, is_active) VALUES
(2, 16.0, 3.25, '2024-01-01', NULL, TRUE);  -- 16 oz pack, $3.25 per pack

-- James Miller - Herb Butter
INSERT INTO FORMULATION_VERSIONS (formulation_id, pack_size, unit_price, effective_from, effective_to, is_active) VALUES
(3, 8.0, 4.00, '2024-01-01', NULL, TRUE);  -- 8 oz pack, $4.00 per pack

-- Sarah Williams - Macaroni
INSERT INTO FORMULATION_VERSIONS (formulation_id, pack_size, unit_price, effective_from, effective_to, is_active) VALUES
(4, 32.0, 2.50, '2024-01-01', NULL, TRUE);  -- 32 oz pack, $2.50 per pack

-- Sarah Williams - Cheddar Cheese
INSERT INTO FORMULATION_VERSIONS (formulation_id, pack_size, unit_price, effective_from, effective_to, is_active) VALUES
(5, 16.0, 6.00, '2024-01-01', NULL, TRUE);  -- 16 oz pack, $6.00 per pack

-- Insert Ingredient Batches
-- James Miller batches (supplier_id = 21)
INSERT INTO INGREDIENT_BATCHES (ingredient_id, supplier_id, version_id, lot_number, quantity_on_hand, cost_per_unit, expiration_date, received_date) VALUES
-- Beef Steak batches
(1, 21, NULL, '1-21-B0001', 1000.0, 8.50, '2024-06-01', '2024-01-15'),
(1, 21, NULL, '1-21-B0002', 800.0, 8.75, '2024-07-01', '2024-02-10'),
-- Seasoning Blend batches
(20, 21, 1, '20-21-B0001', 500.0, 0.55, '2024-08-01', '2024-01-20'),  -- $5.50 per 10 oz pack = $0.55/oz
(20, 21, 1, '20-21-B0002', 300.0, 0.55, '2024-09-01', '2024-02-15'),
-- Brown Gravy batches
(11, 21, 2, '11-21-B0001', 600.0, 0.203125, '2024-08-15', '2024-01-25'),  -- $3.25 per 16 oz pack = $0.203125/oz
(11, 21, 2, '11-21-B0002', 400.0, 0.203125, '2024-09-15', '2024-02-20'),
-- Herb Butter batches
(12, 21, 3, '12-21-B0001', 350.0, 0.50, '2024-07-15', '2024-01-30'),  -- $4.00 per 8 oz pack = $0.50/oz
(12, 21, 3, '12-21-B0002', 250.0, 0.50, '2024-08-15', '2024-02-25');

-- Sarah Williams batches (supplier_id = 22)
INSERT INTO INGREDIENT_BATCHES (ingredient_id, supplier_id, version_id, lot_number, quantity_on_hand, cost_per_unit, expiration_date, received_date) VALUES
-- Macaroni batches
(13, 22, 4, '13-22-B0001', 2000.0, 0.078125, '2024-10-01', '2024-01-20'),  -- $2.50 per 32 oz pack = $0.078125/oz
(13, 22, 4, '13-22-B0002', 1500.0, 0.078125, '2024-11-01', '2024-02-10'),
-- Cheddar Cheese batches
(14, 22, 5, '14-22-B0001', 800.0, 0.375, '2024-08-01', '2024-01-25'),  -- $6.00 per 16 oz pack = $0.375/oz
(14, 22, 5, '14-22-B0002', 600.0, 0.375, '2024-09-01', '2024-02-15'),
-- Potatoes batches
(10, 22, NULL, '10-22-B0001', 1200.0, 0.15, '2024-07-01', '2024-01-18'),
(10, 22, NULL, '10-22-B0002', 900.0, 0.15, '2024-08-01', '2024-02-12');

-- Mike Brown batches (supplier_id = 23)
INSERT INTO INGREDIENT_BATCHES (ingredient_id, supplier_id, version_id, lot_number, quantity_on_hand, cost_per_unit, expiration_date, received_date) VALUES
-- Chocolate batches
(15, 23, NULL, '15-23-B0001', 400.0, 1.25, '2024-09-01', '2024-02-01'),
(15, 23, NULL, '15-23-B0002', 300.0, 1.25, '2024-10-01', '2024-02-20'),
-- Sugar batches
(5, 23, NULL, '5-23-B0001', 1000.0, 0.10, '2024-12-01', '2024-01-15'),
(5, 23, NULL, '5-23-B0002', 800.0, 0.10, '2025-01-01', '2024-02-10');

-- Insert Recipe Plans
-- Steak Dinner (product_id = 100) - Version 1
INSERT INTO RECIPE_PLANS (product_id, version_number, created_date, is_active) VALUES
(100, 1, '2024-01-16', TRUE);

-- Steak Dinner Recipe Ingredients (per unit)
INSERT INTO RECIPE_INGREDIENTS (plan_id, ingredient_id, quantity_required) VALUES
(1, 1, 8.0),   -- 8 oz Beef Steak
(1, 20, 1.0),  -- 1 oz Seasoning Blend
(1, 11, 4.0),  -- 4 oz Brown Gravy
(1, 10, 6.0),  -- 6 oz Potatoes (from Sarah Williams)
(1, 12, 2.0);  -- 2 oz Herb Butter

-- Mac & Cheese (product_id = 2) - Version 1
INSERT INTO RECIPE_PLANS (product_id, version_number, created_date, is_active) VALUES
(2, 1, '2024-01-21', TRUE);

-- Mac & Cheese Recipe Ingredients
INSERT INTO RECIPE_INGREDIENTS (plan_id, ingredient_id, quantity_required) VALUES
(2, 13, 6.0),  -- 6 oz Macaroni
(2, 14, 4.0),  -- 4 oz Cheddar Cheese
(2, 7, 1.0),   -- 1 oz Butter
(2, 8, 2.0);   -- 2 oz Milk

-- Chocolate Lava Cake (product_id = 3) - Version 1
INSERT INTO RECIPE_PLANS (product_id, version_number, created_date, is_active) VALUES
(3, 1, '2024-02-02', TRUE);

-- Chocolate Lava Cake Recipe Ingredients
INSERT INTO RECIPE_INGREDIENTS (plan_id, ingredient_id, quantity_required) VALUES
(3, 15, 3.0),  -- 3 oz Chocolate
(3, 5, 2.0),   -- 2 oz Sugar
(3, 6, 1.5),   -- 1.5 oz Flour
(3, 7, 1.0),   -- 1 oz Butter
(3, 16, 1.0),  -- 1 oz Eggs
(3, 17, 0.1);  -- 0.1 oz Vanilla Extract

-- Chicken Dinner (product_id = 4) - Version 1
INSERT INTO RECIPE_PLANS (product_id, version_number, created_date, is_active) VALUES
(4, 1, '2024-01-11', TRUE);

-- Chicken Dinner Recipe Ingredients
INSERT INTO RECIPE_INGREDIENTS (plan_id, ingredient_id, quantity_required) VALUES
(4, 9, 7.0),   -- 7 oz Chicken Breast
(4, 20, 0.8),  -- 0.8 oz Seasoning Blend
(4, 10, 5.0),  -- 5 oz Potatoes
(4, 11, 3.0);  -- 3 oz Brown Gravy

-- Insert Product Batches
-- Steak Dinner batches (product_id = 100, manufacturer_id = 1)
-- Batch 1: 500 units (standard batch size)
INSERT INTO PRODUCT_BATCHES (product_id, plan_id, batch_number, quantity_produced, total_cost, cost_per_unit, production_date, expiration_date) VALUES
(100, 1, '100-1-B0001', 500, 6250.0, 12.50, '2024-02-01', '2024-05-01');

-- Batch Consumption for Steak Dinner Batch 1
INSERT INTO BATCH_CONSUMPTION (product_batch_id, ingredient_batch_id, quantity_used) VALUES
(1, 1, 4000.0),  -- 500 units * 8 oz = 4000 oz Beef Steak (from lot 1-21-B0001)
(1, 3, 500.0),   -- 500 units * 1 oz = 500 oz Seasoning Blend (from lot 20-21-B0001)
(1, 5, 2000.0),  -- 500 units * 4 oz = 2000 oz Brown Gravy (from lot 11-21-B0001)
(1, 11, 3000.0), -- 500 units * 6 oz = 3000 oz Potatoes (from lot 10-22-B0001)
(1, 7, 1000.0);  -- 500 units * 2 oz = 1000 oz Herb Butter (from lot 12-21-B0001)

-- Update ingredient batch quantities (simulated consumption)
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 4000.0 WHERE ingredient_batch_id = 1;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 500.0 WHERE ingredient_batch_id = 3;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 2000.0 WHERE ingredient_batch_id = 5;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 3000.0 WHERE ingredient_batch_id = 11;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1000.0 WHERE ingredient_batch_id = 7;

-- Steak Dinner Batch 2: 1000 units (2x standard batch size) - This will be the "last batch" for Query 1
INSERT INTO PRODUCT_BATCHES (product_id, plan_id, batch_number, quantity_produced, total_cost, cost_per_unit, production_date, expiration_date) VALUES
(100, 1, '100-1-B0002', 1000, 12500.0, 12.50, '2024-02-15', '2024-05-15');

-- Batch Consumption for Steak Dinner Batch 2
INSERT INTO BATCH_CONSUMPTION (product_batch_id, ingredient_batch_id, quantity_used) VALUES
(2, 2, 8000.0),  -- 1000 units * 8 oz = 8000 oz Beef Steak (from lot 1-21-B0002)
(2, 4, 1000.0),  -- 1000 units * 1 oz = 1000 oz Seasoning Blend (from lot 20-21-B0002)
(2, 6, 4000.0),  -- 1000 units * 4 oz = 4000 oz Brown Gravy (from lot 11-21-B0002)
(2, 12, 6000.0), -- 1000 units * 6 oz = 6000 oz Potatoes (from lot 10-22-B0002)
(2, 8, 2000.0);  -- 1000 units * 2 oz = 2000 oz Herb Butter (from lot 12-21-B0002)

-- Update ingredient batch quantities
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 8000.0 WHERE ingredient_batch_id = 2;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1000.0 WHERE ingredient_batch_id = 4;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 4000.0 WHERE ingredient_batch_id = 6;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 6000.0 WHERE ingredient_batch_id = 12;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 2000.0 WHERE ingredient_batch_id = 8;

-- Steak Dinner Batch 3: 500 units - This will be used for Query 3 (lot number 100-MFG001-B0901)
-- Note: manufacturer_id = 1 corresponds to MFG001
-- Let's create a batch with the exact lot number from Query 3
INSERT INTO PRODUCT_BATCHES (product_id, plan_id, batch_number, quantity_produced, total_cost, cost_per_unit, production_date, expiration_date) VALUES
(100, 1, '100-1-B0901', 500, 6250.0, 12.50, '2024-02-20', '2024-05-20');

-- Batch Consumption for this batch
INSERT INTO BATCH_CONSUMPTION (product_batch_id, ingredient_batch_id, quantity_used) VALUES
(3, 1, 2000.0),  -- Partial consumption from remaining stock
(3, 3, 250.0),
(3, 5, 1000.0),
(3, 11, 1500.0),
(3, 7, 500.0);

-- Update quantities
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 2000.0 WHERE ingredient_batch_id = 1;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 250.0 WHERE ingredient_batch_id = 3;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1000.0 WHERE ingredient_batch_id = 5;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1500.0 WHERE ingredient_batch_id = 11;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 500.0 WHERE ingredient_batch_id = 7;

-- Mac & Cheese batches (product_id = 2, manufacturer_id = 1)
INSERT INTO PRODUCT_BATCHES (product_id, plan_id, batch_number, quantity_produced, total_cost, cost_per_unit, production_date, expiration_date) VALUES
(2, 2, '2-1-B0001', 300, 1200.0, 4.00, '2024-02-10', '2024-04-10');

-- Batch Consumption for Mac & Cheese
INSERT INTO BATCH_CONSUMPTION (product_batch_id, ingredient_batch_id, quantity_used) VALUES
(4, 9, 1800.0),  -- 300 units * 6 oz = 1800 oz Macaroni
(4, 13, 1200.0), -- 300 units * 4 oz = 1200 oz Cheddar Cheese
(4, 15, 300.0),  -- 300 units * 1 oz = 300 oz Butter (using batch from different supplier)
(4, 16, 600.0);  -- 300 units * 2 oz = 600 oz Milk

-- Update quantities
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1800.0 WHERE ingredient_batch_id = 9;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1200.0 WHERE ingredient_batch_id = 13;
-- Note: Butter and Milk batches would need to be added if not present

-- Chicken Dinner batches (product_id = 4, manufacturer_id = 2) - for Query 2
INSERT INTO PRODUCT_BATCHES (product_id, plan_id, batch_number, quantity_produced, total_cost, cost_per_unit, production_date, expiration_date) VALUES
(4, 4, '4-2-B0001', 500, 4500.0, 9.00, '2024-02-05', '2024-05-05');

-- Batch Consumption for Chicken Dinner (uses ingredients from James Miller and Sarah Williams)
INSERT INTO BATCH_CONSUMPTION (product_batch_id, ingredient_batch_id, quantity_used) VALUES
(5, 1, 3500.0),  -- 500 units * 7 oz = 3500 oz Chicken (would need chicken batch, using beef batch as placeholder)
(5, 3, 400.0),   -- 500 units * 0.8 oz = 400 oz Seasoning Blend
(5, 11, 1500.0), -- 500 units * 5 oz = 2500 oz Potatoes (using existing batch)
(5, 5, 1500.0);  -- 500 units * 3 oz = 1500 oz Brown Gravy

-- Update quantities
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 400.0 WHERE ingredient_batch_id = 3;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1500.0 WHERE ingredient_batch_id = 11;
UPDATE INGREDIENT_BATCHES SET quantity_on_hand = quantity_on_hand - 1500.0 WHERE ingredient_batch_id = 5;

-- Insert Do-Not-Combine Rules
-- These are general incompatibility rules (not supplier-specific)
INSERT INTO DO_NOT_COMBINE (ingredient1_id, ingredient2_id, reason, created_date) VALUES
(1, 18, 'Beef and Fish should not be combined due to allergen concerns', '2024-01-01'),
(15, 2, 'Chocolate and Salt have conflicting flavor profiles', '2024-01-01'),
(9, 18, 'Chicken and Fish should not be combined', '2024-01-01'),
(20, 21, 'Seasoning Blend and Tomato Sauce are incompatible', '2024-01-01');

-- Note: For Query 4, we need ingredients in batch 100-MFG001-B0901 (product_batch_id = 3)
-- The batch contains: Beef Steak (1), Seasoning Blend (20), Brown Gravy (11), Potatoes (10), Herb Butter (12)
-- Based on do-not-combine rules, ingredients that conflict:
-- - Fish Fillet (18) conflicts with Beef Steak (1)
-- - Salt (2) conflicts with Chocolate (15) - but Chocolate is not in the batch, so this doesn't apply
-- - Fish Fillet (18) conflicts with Chicken (9) - but Chicken is not in the batch
-- - Tomato Sauce (21) conflicts with Seasoning Blend (20) - this applies!

-- So for Query 4, the conflicting ingredients would be: Fish Fillet (18) and Tomato Sauce (21)
