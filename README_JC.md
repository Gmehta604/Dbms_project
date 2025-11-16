CSC540: Inventory Management Database Project

This project implements the backend database (schema, triggers, and stored procedures) for an inventory management system for a prepared meals manufacturer.

This README is the "owner's manual" for the application development team.

Project Structure

.
├── sql_src/
│ ├── schema.sql # (1) All CREATE TABLE statements
│ ├── procedures_triggers.sql # (2) All Triggers & Stored Procedures
│ ├── populate.sql # (3) Sample data
│ └── test.sql # (4) MASTER BUILD & TEST SCRIPT
│
├── main.py # (To be built by App Team)
├── requirements.txt # (Python packages)
└── README.md # This file

1. Quick Start: How to Build & Test the DB

Follow these steps to get a complete, working, and populated database on your local machine.

Prerequisites

Python 3.x

A running MySQL or MariaDB server

Step 1: Python Virtual Environment (Venv)

This project uses a virtual environment to manage dependencies.

# 1. Create the virtual environment

python3 -m venv venv

# 2. Activate it

# On macOS/Linux:

source venv/bin/activate

# On Windows:

# .\venv\Scripts\activate

# 3. Install the required Python packages

pip install -r requirements.txt

Step 2: Database Configuration

This project was built assuming a local MySQL server with user root.

If your root user (or a different user) has a password, you will be prompted for it. The only file you might need to edit is sql_src/test.sql. If you are not using the user root, change the -u root part of the command in the next step.

Step 3: Build & Test the Database (The "One-Button" Build)

You do not need to run the .sql files one by one. The test.sql script does everything for you.

From your terminal (with your venv activated), run this single command:

# This command will:

# 1. DROP the 'Meal_Manufacturer' database (if it exists)

# 2. CREATE a fresh 'Meal_Manufacturer' database

# 3. BUILD the schema (runs schema.sql)

# 4. BUILD the logic (runs procedures_triggers.sql)

# 5. POPULATE the tables (runs populate.sql)

# 6. RUN all tests to prove it works

mysql -v -u root -p Meal_Manufacturer < sql_src/test.sql

(You will be prompted for your MySQL password)

After you run this, you will have a complete, fully-tested database ready for the application.

2. Database "API" Guide (For App Developers)

The database is built with a "smart" backend. Your Python code should not UPDATE inventory or build lot_number strings. The database handles this automatically.

"Automatic" Triggers (What You Don't Need to Code)

You DO NOT need to write Python code for the following. The database does it for you.

Lot Number Creation:

What you do: INSERT into IngredientBatch or ProductBatch with the "parts" (e.g., product_id, manufacturer_id, manufacturer_batch_id).

What the DB does: trg_compute_product_lot_number automatically builds the lot_number Primary Key (e.g., "100-MFG001-B0901").

Validation:

What you do: INSERT a row into BatchConsumption.

What the DB does: trg_validate_consumption automatically blocks the INSERT if the ingredient lot is expired or if you try to consume more than quantity_on_hand. Your Python code just needs to catch the mysql.connector.Error.

Inventory Management:

What you do: INSERT a row into BatchConsumption.

What the DB does: trg_maintain_on_hand_CONSUME automatically subtracts the quantity_consumed from the IngredientBatch's stock.

What you do: DELETE a row from BatchConsumption (e.g., for a canceled order).

What the DB does: trg_maintain_on_hand_ADJUST automatically adds the quantity back to the stock.

Stored Procedures (What You "CALL" from Python)

These are the functions you will use. You call them from Python using cursor.callproc('ProcedureName', args_tuple).

1. Record_Production_Batch (The "Engine")

This is the atomic, all-or-nothing procedure for creating a new product batch.

Python Call: cursor.callproc('Record_Production_Batch', args)

Parameters (args tuple):

p_product_id (str): e.g., '100'

p_manufacturer_id (str): e.g., 'MFG001'

p_manufacturer_batch_id (str): The new batch ID you create (e.g., 'B0902')

p_produced_quantity (int): e.g., 100

p_expiration_date (str): e.g., '2026-12-01'

p_recipe_id_used (int): e.g., 1

p_consumption_list (str): A JSON string of the "consumption plan."

On Success: The procedure commits all changes.

On Failure: (e.g., health risk, not enough stock) The procedure rolls back all changes and raises a mysql.connector.Error that your Python code must try...except to catch.

2. Trace_Recall (The "Search")

This finds all affected products from a recalled ingredient lot.

Python Call: cursor.callproc('Trace_Recall', args)

Parameters (args tuple):

p_ingredient_lot_number (str): e.g., '106-20-B0006'

p_recall_date (str): e.g., '2025-09-30'

Returns: A result set that you can fetch with cursor.stored_results().

3. Evaluate_Health_Risk

You do not need to call this. This procedure is called internally by Record_Production_Batch.

3. Your Main Task (App Dev Team)

Your most complex task is to build the "Create Product Batch" workflow in Python. This workflow is responsible for building the JSON string that Record_Production_Batch needs.

"Create Product Batch" Python Workflow:

Get Input: Ask the user for product_id ('100') and produced_quantity (100).

Validate Quantity: (In Python) Query Product for its standard_batch_size (100) and check if 100 % 100 == 0.

Get Recipe: (In Python) Query RecipeIngredient for the recipe for this product (Recipe 1).

Calculate Totals: (In Python) Calculate the total generic quantity needed (e.g., 600oz of '106'-Beef, 20oz of '201'-Seasoning).

Run FEFO (First-Expired, First-Out) Logic:

For each generic ingredient (e.g., "600oz of '106'-Beef"):

Query IngredientBatch for all available lots of '106', ORDER BY expiration_date ASC.

Loop through the results and "auto-select" lots until the 600oz is met.

If you can't meet the 600oz, stop and tell the user "Not enough '106'-Beef in stock."

Build the JSON:

After your FEFO logic has successfully built a "consumption plan," create a Python list of dictionaries:

consumption_plan = [
{"lot": "106-20-B0005", "qty": 600}, # From FEFO
{"lot": "201-20-B0001", "qty": 20} # From FEFO
]

Convert it to a JSON string: json_string = json.dumps(consumption_plan)

CALL the Procedure:

Gather all your other parameters (product_id, manufacturer_id, etc.).

Create your args tuple, including json_string as the last item.

Call cursor.callproc('Record_Production_Batch', args) inside a try...except block to catch any errors.
