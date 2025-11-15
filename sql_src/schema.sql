-- =====================================================================
-- 1. USER AND ROLE MANAGEMENT
-- =====================================================================

CREATE TABLE Manufacturer (
    manufacturer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
    -- Other manufacturer details (address, etc.) could go here
);

CREATE TABLE Supplier (
    supplier_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
    -- Other supplier details
);

-- Handles the login and role for all users
CREATE TABLE AppUser (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    -- This role determines which menu the user sees
    role ENUM('Manufacturer', 'Supplier', 'Viewer') NOT NULL,
    
    -- These FKs link a user login to their specific company profile
    -- A user can only be one role, so only one of these will be non-NULL.
    manufacturer_id VARCHAR(20) NULL,
    supplier_id VARCHAR(20) NULL,
    
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturer(manufacturer_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    -- A CHECK constraint to ensure a user isn't both a supplier AND a manufacturer
    CONSTRAINT chk_user_role CHECK (
        (role = 'Manufacturer' AND manufacturer_id IS NOT NULL AND supplier_id IS NULL) OR
        (role = 'Supplier' AND supplier_id IS NOT NULL AND manufacturer_id IS NULL) OR
        (role = 'Viewer' AND manufacturer_id IS NULL AND supplier_id IS NULL)
    )
);

-- =====================================================================
-- 2. PRODUCT & RECIPE DEFINITIONS (The "Templates")
-- =====================================================================

CREATE TABLE Category (
    category_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Ingredient (
    ingredient_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    -- This 'type' is critical for the "no grandchildren" rule
    ingredient_type ENUM('atomic', 'compound') NOT NULL
);

CREATE TABLE Product (
    product_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    
    -- FK to link to a category (e.g., 'Dinners')
    category_id VARCHAR(20) NOT NULL,
    -- FK to establish product "ownership" by a manufacturer
    manufacturer_id VARCHAR(20) NOT NULL,
    
    -- Rule: We must store this to check for "integer multiple" production
    -- Rule: Also used for the "nearly-out-of-stock" report
    standard_batch_size INT NOT NULL CHECK (standard_batch_size > 0),
    
    FOREIGN KEY (category_id) REFERENCES Category(category_id),
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturer(manufacturer_id)
);

-- Stores the "template" for a product (e.g., "v1 Steak Dinner")
-- This allows a Product to have multiple recipe versions over time
CREATE TABLE Recipe (
    recipe_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL, -- e.g., "v1-standard", "v2-low-sodium"
    creation_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE, -- Good for knowing which to use
    
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    UNIQUE KEY (product_id, name) -- A product can't have two recipes named "v1"
);

-- Linking table for the manufacturer's BOM (Recipe -> Ingredients)
CREATE TABLE RecipeIngredient (
    recipe_id INT NOT NULL,
    ingredient_id VARCHAR(20) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL, -- e.g., 'g', 'lbs', 'oz'
    
    PRIMARY KEY (recipe_id, ingredient_id),
    FOREIGN KEY (recipe_id) REFERENCES Recipe(recipe_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id)
);

-- =====================================================================
-- 3. SUPPLIER FORMULATIONS (Supplier-specific Ingredient definitions)
-- =====================================================================

-- This is the supplier's "offer" for an ingredient
CREATE TABLE Formulation (
    formulation_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_id VARCHAR(20) NOT NULL,
    ingredient_id VARCHAR(20) NOT NULL,
    
    pack_size VARCHAR(50) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    
    -- Used for versioning and selecting the "active" formulation
    valid_from_date DATE NOT NULL,
    valid_to_date DATE, -- NULL means it's currently active
    
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id)
    -- We need a TRIGGER to prevent overlapping date ranges for the same (supplier, ingredient) pair
);

-- Linking table for the supplier's "nested BOM"
-- This REPLACES our initial 'CompoundIngredientMaterials' idea
CREATE TABLE FormulationMaterials (
    formulation_id INT NOT NULL,
    material_ingredient_id VARCHAR(20) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    
    PRIMARY KEY (formulation_id, material_ingredient_id),
    FOREIGN KEY (formulation_id) REFERENCES Formulation(formulation_id),
    -- This FK points to the 'atomic' child ingredient
    FOREIGN KEY (material_ingredient_id) REFERENCES Ingredient(ingredient_id)
    -- We need a TRIGGER/CHECK to enforce the "no grandchildren" rule:
    -- 'material_ingredient_id' MUST be of 'atomic' type.
);

-- =====================================================================
-- 4. INVENTORY & TRACEABILITY (The "Physical" Lots)
-- =====================================================================

-- Physical inventory of raw materials from suppliers
CREATE TABLE IngredientBatch (
    -- PK: This is the composite, human-readable ID
    lot_number VARCHAR(255) PRIMARY KEY,
    
    -- These are the "parts" used to build the PK
    ingredient_id VARCHAR(20) NOT NULL,
    supplier_id VARCHAR(20) NOT NULL,
    supplier_batch_id VARCHAR(100) NOT NULL, -- The ID from the supplier's bag
    
    quantity_on_hand DECIMAL(10, 2) NOT NULL,
    per_unit_cost DECIMAL(10, 2) NOT NULL,
    expiration_date DATE NOT NULL,
    
    -- Rule: We must store this to check the "90-day" intake rule
    intake_date DATE NOT NULL,
    
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    -- Ensures you can't have two 'B001' batches for the same ingredient from the same supplier
    UNIQUE KEY (ingredient_id, supplier_id, supplier_batch_id) 
);

-- Physical inventory of finished goods made by the manufacturer
CREATE TABLE ProductBatch (
    -- PK: This is the composite, human-readable ID
    lot_number VARCHAR(255) PRIMARY KEY,
    
    -- These are the "parts" used to build the PK
    product_id VARCHAR(20) NOT NULL,
    manufacturer_id VARCHAR(20) NOT NULL,
    manufacturer_batch_id VARCHAR(100) NOT NULL, -- Your internal batch ID
    
    produced_quantity INT NOT NULL,
    expiration_date DATE NOT NULL,
    
    -- Rule: We must store this for the "recall time window"
    production_date DATETIME NOT NULL,
    
    -- Rule: We store this after calculating it
    total_batch_cost DECIMAL(10, 2),
    
    -- Good practice: Store which recipe version was used for this batch
    recipe_id_used INT NOT NULL,
    
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturer(manufacturer_id),
    FOREIGN KEY (recipe_id_used) REFERENCES Recipe(recipe_id),
    UNIQUE KEY (product_id, manufacturer_id, manufacturer_batch_id)
);

-- This is the MOST IMPORTANT table for traceability
-- It's the "glue" between IngredientBatches and ProductBatches
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

-- Stores the (ingredient_a, ingredient_b) incompatible pairs
CREATE TABLE DoNotCombine (
    ingredient_a_id VARCHAR(20) NOT NULL,
    ingredient_b_id VARCHAR(20) NOT NULL,
    
    PRIMARY KEY (ingredient_a_id, ingredient_b_id),
    FOREIGN KEY (ingredient_a_id) REFERENCES Ingredient(ingredient_id),
    FOREIGN KEY (ingredient_b_id) REFERENCES Ingredient(ingredient_id),
    -- This prevents duplicate pairs (A,B) and (B,A)
    CONSTRAINT chk_ingredient_order CHECK (ingredient_a_id < ingredient_b_id)
);