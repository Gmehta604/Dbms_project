-- ============================================
-- MEAL MANUFACTURER DATABASE SCHEMA
-- Created from ER Diagram
-- ============================================

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS Meal_Manufacturer;
USE Meal_Manufacturer;

CREATE TABLE Users (
    user_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Manufacturer', 'Supplier', 'Viewer') NOT NULL,
    name VARCHAR(150),
    contact_info VARCHAR(255)
);

-- 3. MANUFACTURERS
-- Note: manufacturer_id is NOT AUTO_INCREMENT because sample data uses explicit IDs (1, 2)
CREATE TABLE Manufacturers (
    manufacturer_id INT PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL UNIQUE,
    manufacturer_name VARCHAR(150),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Suppliers (
    supplier_id INT PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(150),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- 5. CATEGORIES
-- Note: category_id is NOT AUTO_INCREMENT because sample data uses explicit IDs (2, 3)
CREATE TABLE Categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

-- 6. PRODUCTS
-- Note: product_id is NOT AUTO_INCREMENT because sample data uses explicit IDs (100, 101)
CREATE TABLE Products (
    product_id INT PRIMARY KEY,
    product_number VARCHAR(50) UNIQUE,
    manufacturer_id INT NOT NULL,
    category_id INT NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    standard_batch_size INT NOT NULL,
    created_date DATE,
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturers(manufacturer_id),
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

-- 7. INGREDIENTS
-- Note: ingredient_id is NOT AUTO_INCREMENT because sample data uses explicit IDs (101, 102, 104, 106, 108, 201, 301)
CREATE TABLE Ingredients (
    ingredient_id INT PRIMARY KEY,
    ingredient_name VARCHAR(150) NOT NULL,
    ingredient_type ENUM('Atomic','Compound') NOT NULL,
    unit_of_measure VARCHAR(50),
    description TEXT
);

-- 8. INGREDIENT_COMPOSITIONS (parent -> child relationship)
CREATE TABLE Ingredient_Compositions (
    parent_ingredient_id INT,
    child_ingredient_id INT,
    quantity_required DECIMAL(10,2),
    PRIMARY KEY (parent_ingredient_id, child_ingredient_id),
    FOREIGN KEY (parent_ingredient_id) REFERENCES Ingredients(ingredient_id),
    FOREIGN KEY (child_ingredient_id) REFERENCES Ingredients(ingredient_id)
);

-- 9. SUPPLIER_INGREDIENTS
CREATE TABLE Supplier_Ingredients (
    supplier_id INT,
    ingredient_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (supplier_id, ingredient_id),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id)
);

CREATE TABLE Formulations (
    formulation_id INT PRIMARY KEY,
    supplier_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    name VARCHAR(150),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id)
);

-- 11. FORMULATION_VERSIONS
CREATE TABLE Formulation_Versions (
    version_id INT PRIMARY KEY,
    formulation_id INT NOT NULL,
    version_no INT NOT NULL,
    pack_size DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    effective_from DATE,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (formulation_id) REFERENCES Formulations(formulation_id),
    UNIQUE KEY uniq_formulation_version (formulation_id, version_no)
);

CREATE TABLE Ingredient_Batches (
    lot_number VARCHAR(100) PRIMARY KEY,
    ingredient_id INT NOT NULL,
    supplier_id INT NOT NULL,
    version_id INT,
    quantity_on_hand DECIMAL(10,2),
    cost_per_unit DECIMAL(10,2),
    expiration_date DATE,
    received_date DATE,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
    FOREIGN KEY (version_id) REFERENCES Formulation_Versions(version_id)
);

-- 13. RECIPE_PLANS
CREATE TABLE Recipe_Plans (
    plan_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    version_number INT NOT NULL,
    created_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- 14. RECIPE_INGREDIENTS
CREATE TABLE Recipe_Ingredients (
    plan_id INT,
    ingredient_id INT,
    quantity_required DECIMAL(10,2),
    PRIMARY KEY (plan_id, ingredient_id),
    FOREIGN KEY (plan_id) REFERENCES Recipe_Plans(plan_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id)
);

CREATE TABLE Product_Batches (
    batch_number VARCHAR(100) PRIMARY KEY,
    product_id INT NOT NULL,
    plan_id INT NOT NULL,
    quantity_produced INT,
    total_cost DECIMAL(12,2),
    cost_per_unit DECIMAL(12,2),
    production_date DATE,
    expiration_date DATE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (plan_id) REFERENCES Recipe_Plans(plan_id)
);

-- 16. BATCH_CONSUMPTION
CREATE TABLE Batch_Consumption (
    product_batch_number VARCHAR(100),
    ingredient_lot_number VARCHAR(100),
    quantity_used DECIMAL(10,2),
    PRIMARY KEY (product_batch_number, ingredient_lot_number),
    FOREIGN KEY (product_batch_number) REFERENCES Product_Batches(batch_number),
    FOREIGN KEY (ingredient_lot_number) REFERENCES Ingredient_Batches(lot_number)
);

-- 17. DO_NOT_COMBINE
CREATE TABLE Do_Not_Combine (
    supplier_id INT NOT NULL,
    ingredient1_id INT NOT NULL,
    ingredient2_id INT NOT NULL,
    reason VARCHAR(255),
    created_date DATE,
    PRIMARY KEY (supplier_id, ingredient1_id, ingredient2_id),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
    FOREIGN KEY (ingredient1_id) REFERENCES Ingredients(ingredient_id),
    FOREIGN KEY (ingredient2_id) REFERENCES Ingredients(ingredient_id)
);

-- ============================================
-- CONSTRAINTS
-- ============================================

-- USERS
ALTER TABLE Users
  ADD CONSTRAINT chk_username_length CHECK (CHAR_LENGTH(username) > 0),
  ADD CONSTRAINT chk_password_length CHECK (CHAR_LENGTH(password) >= 8);

-- MANUFACTURERS
ALTER TABLE Manufacturers
  ADD CONSTRAINT chk_manufacturer_name CHECK (manufacturer_name IS NULL OR CHAR_LENGTH(manufacturer_name) > 0);

-- SUPPLIERS
ALTER TABLE Suppliers
  ADD CONSTRAINT chk_supplier_name CHECK (supplier_name IS NULL OR CHAR_LENGTH(supplier_name) > 0);

-- CATEGORIES
ALTER TABLE Categories
  ADD CONSTRAINT chk_category_name CHECK (CHAR_LENGTH(category_name) > 0);

-- PRODUCTS
ALTER TABLE Products
  ADD CONSTRAINT chk_product_batch_size CHECK (standard_batch_size > 0),
  ADD CONSTRAINT chk_product_name CHECK (CHAR_LENGTH(product_name) > 0);
  -- Note: Date validation (created_date <= CURRENT_DATE) must be enforced in application code
  -- MySQL/MariaDB CHECK constraints cannot use functions like CURRENT_DATE

-- INGREDIENTS
ALTER TABLE Ingredients
  ADD CONSTRAINT chk_ingredient_name CHECK (CHAR_LENGTH(ingredient_name) > 0);

-- INGREDIENT_COMPOSITIONS
ALTER TABLE Ingredient_Compositions
  ADD CONSTRAINT chk_composition_qty CHECK (quantity_required > 0),
  ADD CONSTRAINT chk_no_self_ref CHECK (parent_ingredient_id <> child_ingredient_id);

-- FORMULATION_VERSIONS
ALTER TABLE Formulation_Versions
  ADD CONSTRAINT chk_form_pack_size CHECK (pack_size > 0),
  ADD CONSTRAINT chk_form_price CHECK (unit_price >= 0),
  ADD CONSTRAINT chk_form_dates CHECK (effective_to IS NULL OR effective_from <= effective_to),
  ADD CONSTRAINT chk_form_version CHECK (version_no > 0);

-- INGREDIENT_BATCHES
ALTER TABLE Ingredient_Batches
  ADD CONSTRAINT chk_ing_batch_qty CHECK (quantity_on_hand >= 0),
  ADD CONSTRAINT chk_ing_batch_cost CHECK (cost_per_unit >= 0),
  ADD CONSTRAINT chk_ing_batch_dates CHECK (
    (received_date IS NULL OR expiration_date IS NULL)
    OR received_date <= expiration_date
  );

-- RECIPE_PLANS
ALTER TABLE Recipe_Plans
  ADD CONSTRAINT chk_recipe_version CHECK (version_number > 0);
  -- Note: Date validation (created_date <= CURRENT_DATE) must be enforced in application code
  -- MySQL/MariaDB CHECK constraints cannot use functions like CURRENT_DATE

-- RECIPE_INGREDIENTS
ALTER TABLE Recipe_Ingredients
  ADD CONSTRAINT chk_recipe_qty CHECK (quantity_required > 0);

-- PRODUCT_BATCHES
ALTER TABLE Product_Batches
  ADD CONSTRAINT chk_prod_batch_qty CHECK (quantity_produced >= 0),
  ADD CONSTRAINT chk_prod_batch_cost CHECK (total_cost >= 0 AND cost_per_unit >= 0),
  ADD CONSTRAINT chk_prod_batch_dates CHECK (
    (production_date IS NULL OR expiration_date IS NULL)
    OR production_date <= expiration_date
  );

-- BATCH_CONSUMPTION
ALTER TABLE Batch_Consumption
  ADD CONSTRAINT chk_batch_consumed CHECK (quantity_used > 0);

-- DO_NOT_COMBINE
ALTER TABLE Do_Not_Combine
  ADD CONSTRAINT chk_no_self_combine CHECK (ingredient1_id <> ingredient2_id);
