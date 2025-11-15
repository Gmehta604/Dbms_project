Project Plan (Phase 2): From Database to Final Application

The database "engine" is complete, tested, and documented in README.md.

This plan outlines the remaining tasks for the application team to build the Python CLI and prepare the final submission materials as required by the project handout.

Task 1: Build the Python Application (CLI)

This is the main development task. The goal is to create a menu-driven Python application (main.py) that uses the mysql-connector-python package (from requirements.txt) to interact with the database.

1.1. Build the Main "Shell" & Connection

Create main.py (This is already done in the scaffold).

Implement the user Login Screen (This is already done in the scaffold).

Implement the main Role Selection Menu (This is already done in the scaffold).

1.2. Implement the "Simple" Functions

These are functions that are mostly simple SELECT queries or INSERTs that rely on our triggers. These are the "fill-in-the-blanks" tasks for Teammate 3.

Supplier Menu (role = 'Supplier'):

Manage Ingredients Supplied: (UI for INSERT/UPDATE on Formulation)

Create Ingredient Batch: (UI for INSERT into IngredientBatch. The triggers do all the work.)

Manufacturer Menu (role = 'Manufacturer'):

Create & Manage Product Types: (UI for INSERT/UPDATE on Product)

Create & Update Recipe Plans: (UI for INSERT on Recipe and RecipeIngredient)

Viewer Menu (role = 'Viewer'):

Browse Product Types: (A SELECT query joining Product, Category, and Manufacturer)

Generate Ingredient List: (A complex SELECT query. See README.md for logic.)

1.3. Implement the "Boss Level" Function (Manufacturer)

Create Product Batch: This is the most complex workflow (Task for Teammate 1).

Your README.md file (Section 3) has the exact 7-step plan for this.

The main.py scaffold already has 90% of this logic written. The developer just needs to finish it.

Task 2: Implement the 5 Required Queries

The handout lists 5 specific queries that must be supported. This is the task for Teammate 2 (run_manufacturer_reports() in main.py).

Here is the starter SQL for each required query:

1. "List the ingredients and the lot number of the last batch of product type Steak Dinner (100) made by manufacturer MFG001."

SELECT
bc.ingredient_lot_number,
i.name
FROM ProductBatch pb
JOIN BatchConsumption bc ON pb.lot_number = bc.product_lot_number
JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
WHERE
pb.product_id = '100'
AND pb.manufacturer_id = 'MFG001'
ORDER BY
pb.production_date DESC
LIMIT 1; -- (Or use a subquery to get the latest production_date)

2. "For manufacturer MFG002, list all the suppliers that they have purchased from and the total amount of money they have spent with that supplier."

-- This query assumes "spent" means the cost of _consumed_ goods.
SELECT
s.name AS supplier_name,
SUM(bc.quantity_consumed \* ib.per_unit_cost) AS total_spent
FROM
BatchConsumption bc
JOIN
ProductBatch pb ON bc.product_lot_number = pb.lot_number
JOIN
IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
JOIN
Supplier s ON ib.supplier_id = s.supplier_id
WHERE
pb.manufacturer_id = 'MFG002'
GROUP BY
s.supplier_id, s.name;

3. "For product with lot number 100-MFG001-B0901, find the unit cost for that product."

SELECT
(total_batch_cost / produced_quantity) AS unit_cost
FROM
ProductBatch
WHERE
lot_number = '100-MFG001-B0901';

4. "Based on the ingredients currently in product lot number 100-MFG001-B0901, what are all ingredients that cannot be included..."
   (This is the hardest query. It requires using the Evaluate_Health_Risk logic.)

-- 1. First, create a temporary table with all atoms in the batch
-- (This logic is copied from your 'Evaluate_Health_Risk' procedure)
CREATE TEMPORARY TABLE Temp_Atoms_In_Batch AS (
-- (Query for all atomic ingredients in '100-MFG001-B0901')
-- ...
-- (Query for all _flattened_ atomic materials from compound ingredients)
-- ...
);

-- 2. Now, find all ingredients that conflict with this list
SELECT
i.ingredient_id,
i.name AS conflicting_ingredient
FROM
Ingredient i
JOIN
DoNotCombine dnc ON i.ingredient_id = dnc.ingredient_a_id
JOIN
Temp_Atoms_In_Batch t ON dnc.ingredient_b_id = t.ingredient_id
WHERE
i.ingredient_id NOT IN (SELECT ingredient_id FROM Temp_Atoms_In_Batch)
UNION
SELECT
i.ingredient_id,
i.name AS conflicting_ingredient
FROM
Ingredient i
JOIN
DoNotCombine dnc ON i.ingredient_id = dnc.ingredient_b_id
JOIN
Temp_Atoms_In_Batch t ON dnc.ingredient_a_id = t.ingredient_id
WHERE
i.ingredient_id NOT IN (SELECT ingredient_id FROM Temp_Atoms_In_Batch);

5. "Which manufacturers have supplier James Miller (21) NOT supplied to?"

-- This query finds all manufacturers...
SELECT m.manufacturer_id, m.name
FROM Manufacturer m
WHERE m.manufacturer_id NOT IN (
-- ...who HAVE used an ingredient from supplier 21
SELECT DISTINCT
pb.manufacturer_id
FROM
BatchConsumption bc
JOIN
IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
JOIN
ProductBatch pb ON bc.product_lot_number = pb.lot_number
WHERE
ib.supplier_id = '21'
);

Task 3: The Final Report (35% of Grade)

This is a CRITICAL deliverable. This is Your (Jon's) Task. You have all the context and files needed.

Updated ER Model: Create a visual diagram of the final schema.

Functional Dependencies: Use the normalization_report.md file. It already contains this analysis.

Normalization Analysis: Use the normalization_report.md file. It proves your schema is in BCNF.

Constraints Analysis: This is the most important part. You must justify why some logic is in the database and some is in the app.

Constraints in the Database (Triggers, PK/FK, Checks):

Referential Integrity (FOREIGN KEY): Guarantees data consistency (e.g., can't consume an IngredientLot that doesn't exist).

Data Integrity (PRIMARY KEY, UNIQUE, NOT NULL): Enforces uniqueness and completeness.

Lot Number Format (trg*compute*...\_lot_number): Guarantees 100% consistency in lot number format, which is critical for joins.

Expiration Check (trg_validate_consumption): A non-negotiable "security guard" rule. The database must block consumption of expired goods, even if the application forgets to check.

Quantity Check (trg_validate_consumption): The final line of defense against race conditions or bugs that could lead to negative inventory.

Health Risk Check (Evaluate_Health_Risk): A critical, non-negotiable business rule that must be enforced at the transaction level.

Constraints in the Application (Python):

FEFO (First-Expired, First-Out): This is not an integrity rule; it's a "polite" business policy. It's complex logic (loops, sorting) that is much easier to write in Python than in a single SQL query.

Standard Batch Size Multiple: The check that produced_quantity % standard_batch_size == 0. This is a simple UI validation. It's an app-level rule, not a database integrity rule (the DB could store it, but the check belongs in the UI for good user feedback).

Task 4: Suggested Team Work Split (The "War Plan")

Person 1 (DBA / You):

Task: Lead author on the Final Report (you have all the context).

Task: Help debug Python code, especially try...except blocks and procedure calls.

Person 2 (App Lead - Manufacturer):

Task: Implement the "Boss Level" Create Product Batch function (Section 1.3). The main.py scaffold is 90% complete.

Person 3 (App Lead - Supplier/Viewer):

Task: Implement the main shell (Login, Menus) and all "Simple" functions for all roles (Section 1.2). Fill in all the Function not yet implemented. stubs except for create_product_batch and run_manufacturer_reports.

Person 4 (Query & Report Lead):

Task: Implement the 5 Required Queries (Section 2) in the run_manufacturer_reports function.

Task: Create the final ER Diagram image for the report.

Task: Prepare the demo script.
