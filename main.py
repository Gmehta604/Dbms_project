import mysql.connector
import getpass
import json
import sys
from datetime import date, timedelta
from tabulate import tabulate # Import at the top

# --- Database Configuration ---
DB_CONFIG = {
    'user': 'root',
    'host': '127.0.0.1',
    'database': 'Meal_Manufacturer'
}

# --- Helper Functions ---
def pretty_print_results(cursor):
    """
    Helper function to print query results in a nice table.
    FIXED: It automatically uses the column names (AS clauses)
    from your SQL query as the headers.
    """
    results = cursor.fetchall()
    if not results:
        print("No results found.")
        return
    
    # "headers='keys'" tells tabulate to use the dictionary keys
    # (i.e., your SQL 'AS' clauses) as the table headers.
    print(tabulate(results, headers="keys", tablefmt="grid"))

# --- Main Application ---

def login(cursor):
    """
    Handles user login, authenticates against the AppUser table,
    and returns the user's session info.
    """
    print("--- Login ---")
    username = input("Username: ")
    password = getpass.getpass("Password: ") 

    query = """
        SELECT role, manufacturer_id, supplier_id 
        FROM AppUser 
        WHERE username = %s AND password_hash = %s
    """
    try:
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        if result:
            role = result.get('role')
            man_id = result.get('manufacturer_id')
            sup_id = result.get('supplier_id')
            user_id = man_id if role == 'Manufacturer' else sup_id
            
            print(f"\nLogin successful. Welcome, {username} (Role: {role})")
            return {
                "username": username,
                "role": role,
                "id": user_id  # This will be 'MFG001' or '20', etc.
            }
        else:
            print("Login failed. Invalid username or password.")
            return None
    except mysql.connector.Error as err:
        print(f"Login error: {err}")
        return None

# =====================================================================
# --- MANUFACTURER MENU ---
# =====================================================================

def create_product_type(cursor, db, user_session):
    """(SIMPLE FUNCTION) - Creates a new product type."""
    print("\n--- (1) Create & Manage Product Types ---")
    try:
        product_id = input("Enter new Product ID (e.g., 102): ")
        name = input("Enter Product Name (e.g., 'Chicken Soup'): ")
        category_id = input("Enter Category ID (e.g., '2' for Dinners): ")
        sbs = int(input("Enter Standard Batch Size (e.g., 150): "))
        manufacturer_id = user_session['id']

        query = """
            INSERT INTO Product 
              (product_id, name, category_id, manufacturer_id, standard_batch_size)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (product_id, name, category_id, manufacturer_id, sbs))
        db.commit()
        print(f"Success! Product '{name}' created.")

    except mysql.connector.Error as err:
        db.rollback()
        print(f"Error: {err.msg}")
    except ValueError:
        print("Error: Standard batch size must be an integer.")

def create_recipe_plan(cursor, db, user_session):
    """(SIMPLE FUNCTION) - Creates a new (versioned) recipe."""
    print("\n--- (2) Create & Update Recipe Plans (Versioned) ---")
    try:
        product_id = input("Enter Product ID to create a recipe for (e.g., 100): ")
        recipe_name = input("Enter new Recipe Name (e.g., 'v2-low-sodium'): ")
        
        # 1. Create the 'parent' Recipe row
        query_recipe = """
            INSERT INTO Recipe (product_id, name, creation_date, is_active)
            VALUES (%s, %s, %s, %s)
        """
        # (We could also have logic to set other recipes for this product to is_active=0)
        cursor.execute(query_recipe, (product_id, recipe_name, date.today(), 1))
        recipe_id = cursor.lastrowid # Get the new PK we just created
        print(f"Created new recipe with ID: {recipe_id}")

        # 2. Loop and add ingredients
        while True:
            print("\nAdd an ingredient to the recipe (or type 'done' to finish):")
            ing_id = input("  Ingredient ID (e.g., 101): ")
            if ing_id.lower() == 'done':
                break
            
            qty = float(input("  Quantity (oz) (e.g., 0.5): "))
            unit = input("  Unit (e.g., 'oz'): ")

            query_ing = """
                INSERT INTO RecipeIngredient (recipe_id, ingredient_id, quantity, unit_of_measure)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query_ing, (recipe_id, ing_id, qty, unit))
            print(f"Added ingredient {ing_id}.")
        
        db.commit()
        print(f"\nSuccess! Recipe '{recipe_name}' (ID: {recipe_id}) created.")
        
    except mysql.connector.Error as err:
        db.rollback()
        print(f"Error: {err.msg}")
    except ValueError:
        db.rollback()
        print("Error: Quantity must be a number.")

def create_product_batch(cursor, db, user_session):
    """(BOSS LEVEL FUNCTION) - This is the most complex workflow."""
    print("\n--- (3) Create Product Batch (Production Posting) ---")
    
    try:
        # --- Step 1: Get Input ---
        product_id = input("Enter Product ID to manufacture (e.g., 100): ")
        produced_quantity = int(input("Enter Production Quantity (e.g., 100): "))
        manufacturer_batch_id = input("Enter new Manufacturer Batch ID (e.g., B0902): ")
        exp_date_str = input("Enter Expiration Date (YYYY-MM-DD): ")
        
        # --- Step 2: Validate Quantity (Python Check) ---
        cursor.execute("SELECT standard_batch_size FROM Product WHERE product_id = %s AND manufacturer_id = %s", 
                       (product_id, user_session['id']))
        sbs_result = cursor.fetchone()
        if not sbs_result:
            print(f"Error: You do not own Product ID {product_id}.")
            return
            
        sbs = sbs_result['standard_batch_size']
        if produced_quantity % sbs != 0:
            print(f"Error: Quantity ({produced_quantity}) must be a multiple of the standard batch size ({sbs}).")
            return

        # --- Step 3: Get Active Recipe ---
        cursor.execute("SELECT recipe_id FROM Recipe WHERE product_id = %s AND is_active = 1 LIMIT 1", (product_id,))
        recipe_result = cursor.fetchone()
        if not recipe_result:
            print(f"Error: No active recipe found for Product ID {product_id}.")
            return
        
        recipe_id_used = recipe_result['recipe_id']
        
        cursor.execute("SELECT ingredient_id, quantity FROM RecipeIngredient WHERE recipe_id = %s", (recipe_id_used,))
        recipe_ingredients = cursor.fetchall()

        # --- Step 4 & 5: Calculate Totals & Run FEFO Logic ---
        print("Calculating inventory requirements...")
        consumption_plan = [] # This will become our JSON
        
        for ingredient in recipe_ingredients:
            ing_id = ingredient['ingredient_id']
            qty_per_unit = ingredient['quantity']
            
            total_needed = qty_per_unit * produced_quantity
            print(f"Need {total_needed} oz of ingredient {ing_id}...")
            
            fefo_query = """
                SELECT lot_number, quantity_on_hand 
                FROM IngredientBatch 
                WHERE ingredient_id = %s 
                  AND quantity_on_hand > 0 
                  AND expiration_date > CURDATE()
                ORDER BY expiration_date ASC
            """
            cursor.execute(fefo_query, (ing_id,))
            available_lots = cursor.fetchall()
            
            if not available_lots:
                print(f"*** CRITICAL ERROR: No available stock for ingredient {ing_id}! ***")
                print("Batch creation cancelled.")
                return

            # --- This is the core FEFO loop ---
            for lot in available_lots:
                lot_number = lot['lot_number']
                lot_qty = lot['quantity_on_hand']

                if total_needed <= 0:
                    break # We have enough of this ingredient
                
                consume_qty = min(lot_qty, total_needed)
                consumption_plan.append({"lot": lot_number, "qty": float(consume_qty)})
                total_needed -= consume_qty
            
            if total_needed > 0:
                print(f"*** CRITICAL ERROR: Not enough stock for ingredient {ing_id}! ***")
                print(f"Only found {qty_per_unit * produced_quantity - total_needed} oz, but still need {total_needed} oz.")
                print("Batch creation cancelled.")
                return

        # --- Step 6: Build the JSON ---
        json_string = json.dumps(consumption_plan)
        print("\nConsumption Plan (JSON):")
        print(json_string)
        
        if input("Do you want to proceed with this batch? (y/n): ").lower() != 'y':
            print("Batch creation cancelled.")
            return

        # --- Step 7: CALL the Stored Procedure ---
        print("Calling Record_Production_Batch...")
        args = (
            product_id,
            user_session['id'],
            manufacturer_batch_id,
            produced_quantity,
            exp_date_str,
            recipe_id_used,
            json_string
        )
        
        # This is how you call the procedure and catch errors!
        cursor.callproc('Record_Production_Batch', args)
        db.commit()
        print("\n*** SUCCESS: Product batch created! ***")

    except mysql.connector.Error as err:
        db.rollback() # Rollback any changes
        print("\n*** ERROR: Batch creation failed! ***")
        print(f"Database error: {err.msg}")
    except Exception as e:
        db.rollback()
        print(f"An unexpected error occurred: {e}")

def run_manufacturer_reports(cursor, db, user_session):
    """(REPORTING FUNCTION) - Runs the 5 required queries."""
    print("\n--- (5) Run Reports ---")
    
    print("\n--- Required Queries ---")
    print("1. Ingredients of last 'Steak Dinner' batch (MFG001)")
    print("2. Suppliers and spending (MFG002)")
    print("3. Unit cost for lot '100-MFG001-B0901'")
    print("4. Conflicting ingredients for lot '100-MFG001-B0901'")
    print("5. Manufacturers not supplied by 'James Miller' (21)")
    print("\n--- Other Health Reports (NEWLY ADDED) ---")
    print("6. Nearly-Out-of-Stock Items (by Product)")
    print("7. Almost-Expired Ingredient Lots (Next 10 Days)")
    
    choice = input("Select a report (1-7): ")
    
    try:
        if choice == '1':
            print("Report 1: Last batch of Steak Dinner (100) by MFG001")
            # FIXED QUERY: This query now finds the MAX date first,
            # then finds all ingredients for the batch(es) with that date.
            query1 = """
                SELECT
                    bc.ingredient_lot_number AS 'Ingredient Lot',
                    i.name AS 'Ingredient Name',
                    pb.production_date AS 'Produced On'
                FROM BatchConsumption bc
                JOIN ProductBatch pb ON bc.product_lot_number = pb.lot_number
                JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
                JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
                WHERE
                    pb.production_date = (
                        SELECT MAX(pb2.production_date)
                        FROM ProductBatch pb2
                        WHERE pb2.product_id = '100'
                        AND pb2.manufacturer_id = 'MFG001'
                    )
                AND pb.product_id = '100'
                AND pb.manufacturer_id = 'MFG001';
            """
            cursor.execute(query1)
            pretty_print_results(cursor)

        elif choice == '2':
            print("Report 2: Total spending by MFG002, by supplier")
            query2 = """
                SELECT
                    s.name AS 'Supplier Name',
                    SUM(bc.quantity_consumed * ib.per_unit_cost) AS 'Total Spent ($)'
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
            """
            cursor.execute(query2)
            pretty_print_results(cursor)

        elif choice == '3':
            print("Report 3: Unit cost for lot '100-MFG001-B0901'")
            query3 = """
                SELECT
                    (total_batch_cost / produced_quantity) AS 'Unit Cost ($)'
                FROM
                    ProductBatch
                WHERE
                    lot_number = '100-MFG001-B0901';
            """
            cursor.execute(query3)
            pretty_print_results(cursor)

        elif choice == '4':
            print("Report 4: Conflicting ingredients for lot '100-MFG001-B0901'")
            
            # =================================================================
            # CLAUDE'S FIX FOR ERROR 1137: "Can't reopen table: 't'"
            # 1. Create all the temporary tables
            # =================================================================
            cursor.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Atoms_In_Batch (
                    ingredient_id VARCHAR(20) PRIMARY KEY
                );
            """)
            cursor.execute("TRUNCATE TABLE Temp_Atoms_In_Batch;")
            
            cursor.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Atoms_In_Batch_2 (
                    ingredient_id VARCHAR(20) PRIMARY KEY
                );
            """)
            cursor.execute("TRUNCATE TABLE Temp_Atoms_In_Batch_2;")
            
            cursor.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Atoms_In_Batch_3 (
                    ingredient_id VARCHAR(20) PRIMARY KEY
                );
            """)
            cursor.execute("TRUNCATE TABLE Temp_Atoms_In_Batch_3;")
            
            cursor.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Atoms_In_Batch_4 (
                    ingredient_id VARCHAR(20) PRIMARY KEY
                );
            """)
            cursor.execute("TRUNCATE TABLE Temp_Atoms_In_Batch_4;")
            
            cursor.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Atoms_In_Batch_5 (
                    ingredient_id VARCHAR(20) PRIMARY KEY
                );
            """)
            cursor.execute("TRUNCATE TABLE Temp_Atoms_In_Batch_5;")
            
            cursor.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS Temp_Conflict_List (
                    ingredient_id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(255)
                );
            """)
            cursor.execute("TRUNCATE TABLE Temp_Conflict_List;")

            # 2. Get all ATOMIC ingredients from the lot
            cursor.execute("""
                INSERT IGNORE INTO Temp_Atoms_In_Batch (ingredient_id)
                SELECT ib.ingredient_id
                FROM BatchConsumption bc
                JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
                JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
                WHERE bc.product_lot_number = '100-MFG001-B0901'
                  AND i.ingredient_type = 'ATOMIC';
            """)
            
            # 3. Get all FLATTENED atomic ingredients from COMPOUND lots
            cursor.execute("""
                INSERT IGNORE INTO Temp_Atoms_In_Batch (ingredient_id)
                SELECT fm.material_ingredient_id
                FROM BatchConsumption bc
                JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
                JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
                JOIN Formulation f ON f.ingredient_id = ib.ingredient_id 
                                   AND f.supplier_id = ib.supplier_id
                                   AND ib.intake_date BETWEEN f.valid_from_date AND COALESCE(f.valid_to_date, '9999-12-31')
                JOIN FormulationMaterials fm ON fm.formulation_id = f.formulation_id
                WHERE bc.product_lot_number = '100-MFG001-B0901'
                  AND i.ingredient_type = 'COMPOUND';
            """)
            
            # 4. Copy data from table 1 into all other temp tables
            cursor.execute("INSERT INTO Temp_Atoms_In_Batch_2 (ingredient_id) SELECT ingredient_id FROM Temp_Atoms_In_Batch;")
            cursor.execute("INSERT INTO Temp_Atoms_In_Batch_3 (ingredient_id) SELECT ingredient_id FROM Temp_Atoms_In_Batch;")
            cursor.execute("INSERT INTO Temp_Atoms_In_Batch_4 (ingredient_id) SELECT ingredient_id FROM Temp_Atoms_In_Batch;")
            cursor.execute("INSERT INTO Temp_Atoms_In_Batch_5 (ingredient_id) SELECT ingredient_id FROM Temp_Atoms_In_Batch;")
            db.commit()

            # 5. SPLIT THE UNION - Execute as two separate INSERT statements
            
            # First part: Find conflicts where ingredient is dnc.ingredient_a_id
            query4_part1 = """
                INSERT IGNORE INTO Temp_Conflict_List (ingredient_id, name)
                SELECT
                    i.ingredient_id,
                    i.name
                FROM
                    Ingredient i
                JOIN
                    DoNotCombine dnc ON i.ingredient_id = dnc.ingredient_a_id
                JOIN
                    Temp_Atoms_In_Batch_2 AS t1 ON dnc.ingredient_b_id = t1.ingredient_id
                WHERE
                    i.ingredient_id NOT IN (SELECT ingredient_id FROM Temp_Atoms_In_Batch_3);
            """
            cursor.execute(query4_part1)
            
            # Second part: Find conflicts where ingredient is dnc.ingredient_b_id
            query4_part2 = """
                INSERT IGNORE INTO Temp_Conflict_List (ingredient_id, name)
                SELECT
                    i.ingredient_id,
                    i.name
                FROM
                    Ingredient i
                JOIN
                    DoNotCombine dnc ON i.ingredient_id = dnc.ingredient_b_id
                JOIN
                    Temp_Atoms_In_Batch_4 AS t_other ON dnc.ingredient_a_id = t_other.ingredient_id
                WHERE
                    i.ingredient_id NOT IN (SELECT ingredient_id FROM Temp_Atoms_In_Batch_5);
            """
            cursor.execute(query4_part2)
            db.commit() # Commit the inserts into the conflict list

            # 6. Select from the simple, final results table
            cursor.execute("SELECT ingredient_id AS 'Conflicting ID', name AS 'Conflicting Ingredient Name' FROM Temp_Conflict_List;")
            pretty_print_results(cursor)

        elif choice == '5':
            print("Report 5: Manufacturers not supplied by 'James Miller' (21)")
            query5 = """
                SELECT 
                    m.manufacturer_id AS 'Manufacturer ID', 
                    m.name AS 'Manufacturer Name'
                FROM Manufacturer m
                WHERE m.manufacturer_id NOT IN (
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
            """
            cursor.execute(query5)
            pretty_print_results(cursor)
        
        # =================================================================
        # NEWLY ADDED REPORTS
        # =================================================================
        elif choice == '6':
            print("Report 6: Nearly-Out-of-Stock Items (by Product)")
            # This query finds all ingredients whose *total stock* is less than
            # the standard_batch_size of *any product that uses it*.
            # This version only shows items relevant to the logged-in manufacturer.
            query6 = """
                SELECT 
                    i.name AS 'Ingredient Name',
                    p.name AS 'Product Name',
                    p.standard_batch_size AS 'Product SBS',
                    COALESCE(SUM(ib.quantity_on_hand), 0) AS 'Total Stock On-Hand'
                FROM 
                    Ingredient i
                JOIN 
                    RecipeIngredient ri ON i.ingredient_id = ri.ingredient_id
                JOIN 
                    Recipe r ON ri.recipe_id = r.recipe_id
                JOIN 
                    Product p ON r.product_id = p.product_id
                LEFT JOIN 
                    IngredientBatch ib ON i.ingredient_id = ib.ingredient_id
                WHERE 
                    p.manufacturer_id = %s -- Only show for products *this* mfg owns
                GROUP BY 
                    i.ingredient_id, i.name, p.product_id, p.name, p.standard_batch_size
                HAVING 
                    `Total Stock On-Hand` < p.standard_batch_size;
            """
            cursor.execute(query6, (user_session['id'],))
            pretty_print_results(cursor)

        elif choice == '7':
            print("Report 7: Almost-Expired Ingredient Lots (Next 10 Days)")
            # Assumes today is 2025-11-15 for test data consistency
            query7 = """
                SELECT 
                    lot_number AS 'Lot Number', 
                    ingredient_id AS 'Ingredient ID',
                    quantity_on_hand AS 'Qty',
                    expiration_date AS 'Expires On'
                FROM 
                    IngredientBatch
                WHERE 
                    expiration_date BETWEEN '2025-11-15' AND ('2025-11-15' + INTERVAL 10 DAY);
            """
            cursor.execute(query7)
            pretty_print_results(cursor)
            
        else:
            print("Invalid choice.")
    
    except mysql.connector.Error as err:
        db.rollback() # Rollback in case of error
        print(f"Report Error: {err.msg}")
    except Exception as e:
        db.rollback() # Rollback in case of error
        print(f"An unexpected error occurred: {e}")

def manufacturer_menu(cursor, db, user_session):
    """Main menu loop for the Manufacturer role."""
    while True:
        print("\n--- Manufacturer Menu ---")
        print("1. Create/Update Product Type")
        print("2. Create/Update Recipe Plan")
        print("3. Create Product Batch (Production Posting)")
        print("4. Run Reports (Required Queries)")
        print("5. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            create_product_type(cursor, db, user_session)
        elif choice == '2':
            create_recipe_plan(cursor, db, user_session)
        elif choice == '3':
            create_product_batch(cursor, db, user_session)
        elif choice == '4':
            # This is the line with the bug fix
            run_manufacturer_reports(cursor, db, user_session)
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

# =====================================================================
# --- SUPPLIER MENU ---
# =====================================================================

def manage_formulations(cursor, db, user_session):
    """(SIMPLE FUNCTION) - Creates a new formulation (supplier 'offer')."""
    print("\n--- (1) Manage Ingredients Supplied (Formulations) ---")
    try:
        ingredient_id = input("Enter Ingredient ID you want to supply (e.g., 101): ")
        pack_size = input("Enter Pack Size (e.g., '10-kg pack'): ")
        unit_price = float(input("Enter Price per Pack (e.g., 25.50): "))
        valid_from_date = input("Enter Valid From Date (YYYY-MM-DD): ")
        valid_to_date = input("Enter Valid To Date (YYYY-MM-DD or leave blank): ")
        
        if valid_to_date == "":
            valid_to_date = None

        query = """
            INSERT INTO Formulation 
              (ingredient_id, supplier_id, pack_size, unit_price, valid_from_date, valid_to_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (ingredient_id, user_session['id'], pack_size, 
                               unit_price, valid_from_date, valid_to_date))
        
        db.commit()
        print("\n*** SUCCESS: New formulation created! ***")
        print("Note: You may now need to define its materials if it's a compound ingredient.")

    except mysql.connector.Error as err:
        db.rollback()
        print(f"Error: {err.msg}")
    except ValueError:
        db.rollback()
        print("Error: Invalid input. Price must be a number.")

def define_formulation_materials(cursor, db, user_session):
    """(SIMPLE FUNCTION) - Defines the 'nested BOM' for a compound formulation."""
    print("\n--- (2) Define Ingredient Materials (For Compound) ---")
    try:
        formulation_id = int(input("Enter Formulation ID to define materials for: "))
        
        # Security check: Does this supplier *own* this formulation?
        cursor.execute("SELECT 1 FROM Formulation WHERE formulation_id = %s AND supplier_id = %s",
                       (formulation_id, user_session['id']))
        if not cursor.fetchone():
            print(f"Error: You do not own Formulation ID {formulation_id}.")
            return
            
        print(f"Defining materials for Formulation ID {formulation_id}...")
        
        # Loop and add materials
        while True:
            print("\nAdd a material to the formulation (or type 'done' to finish):")
            ing_id = input("  Material Ingredient ID (must be ATOMIC, e.g., 101): ")
            if ing_id.lower() == 'done':
                break
            
            qty = float(input("  Quantity (oz) (e.g., 0.5): "))

            query_ing = """
                INSERT INTO FormulationMaterials (formulation_id, material_ingredient_id, quantity)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query_ing, (formulation_id, ing_id, qty))
            print(f"Added material {ing_id}.")
        
        db.commit()
        print(f"\nSuccess! Materials for Formulation ID {formulation_id} saved.")
        
    except mysql.connector.Error as err:
        db.rollback()
        print(f"Error: {err.msg}")
    except ValueError:
        db.rollback()
        print("Error: Quantity must be a number.")

def create_supplier_batch(cursor, db, user_session):
    """(SIMPLE FUNCTION) - Creates a new ingredient batch."""
    print("\n--- (3) Create Ingredient Batch (Lot Intake) ---")
    try:
        ingredient_id = input("Enter Ingredient ID: ")
        
        # Access Control Check: Does this supplier actually supply this ingredient?
        # We check the Formulation table to see if an "offer" exists.
        cursor.execute("""
            SELECT 1 FROM Formulation 
            WHERE supplier_id = %s 
              AND ingredient_id = %s
              AND CURDATE() BETWEEN valid_from_date AND COALESCE(valid_to_date, '9999-12-31')
        """, (user_session['id'], ingredient_id))
        
        if not cursor.fetchone():
            print(f"Error: You are not authorized to supply ingredient {ingredient_id} (or no active formulation exists).")
            return
            
        supplier_batch_id = input("Enter Supplier's Batch ID (e.g., B0010): ")
        quantity = float(input("Enter Quantity (oz): "))
        cost = float(input("Enter Per-Unit Cost (e.g., 0.10): "))
        exp_date_str = input("Enter Expiration Date (YYYY-MM-DD): ")
        
        # Python Check (90-day rule):
        # We'll assume "today" is Nov 15, 2025 for consistency with sample data logic
        intake_date = date(2025, 11, 15)
        expiration_date = date.fromisoformat(exp_date_str)
        if (expiration_date - intake_date).days < 90:
           print(f"Error: Expiration date ({exp_date_str}) must be at least 90 days from today ({intake_date}).")
           return
           
        query = """
            INSERT INTO IngredientBatch 
              (ingredient_id, supplier_id, supplier_batch_id, 
               quantity_on_hand, per_unit_cost, expiration_date, intake_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (ingredient_id, user_session['id'], supplier_batch_id, 
                               quantity, cost, exp_date_str, intake_date))
        
        db.commit()
        print("\n*** SUCCESS: Ingredient batch created! ***")
        # The trigger 'trg_compute_ingredient_lot_number' automatically built the lot_number.

    except mysql.connector.Error as err:
        db.rollback()
        print(f"Error: {err.msg}")
    except ValueError:
        db.rollback()
        print("Error: Invalid input. Quantity/Cost must be numbers. Date must be YYYY-MM-DD.")

def supplier_menu(cursor, db, user_session):
    """(SIMPLE FUNCTIONS) - Menu for Supplier role."""
    while True:
        print("\n--- Supplier Menu ---")
        print("1. Manage Ingredients Supplied (Formulations)")
        print("2. Define Ingredient Materials (For Compound)")
        print("3. Create Ingredient Batch (Lot Intake)")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            manage_formulations(cursor, db, user_session)
        elif choice == '2':
            define_formulation_materials(cursor, db, user_session)
        elif choice == '3':
            create_supplier_batch(cursor, db, user_session)
        elif choice == '4':
            break
        else:
            print("Invalid choice.")

# =====================================================================
# --- VIEWER MENU ---
# =====================================================================

def generate_ingredient_list(cursor, db, user_session):
    """(SIMPLE FUNCTION) - Complex SELECT query."""
    print("\n--- (2) Generate Ingredient List (Flattened) ---")
    
    try:
        product_id = input("Enter Product ID (e.g., 100): ")
        
        # This query is a simplified version of the health risk one.
        # It finds the active recipe, then unnests compound ingredients.
        
        # 1. Get active recipe
        cursor.execute("SELECT recipe_id FROM Recipe WHERE product_id = %s AND is_active = 1 LIMIT 1", (product_id,))
        recipe_result = cursor.fetchone()
        if not recipe_result:
            print(f"Error: No active recipe found for Product ID {product_id}.")
            return
        
        recipe_id = recipe_result['recipe_id']

        # 2. Get all ATOMIC ingredients from the recipe
        query_atomic = """
            SELECT i.name AS name, ri.quantity AS quantity
            FROM RecipeIngredient ri
            JOIN Ingredient i ON ri.ingredient_id = i.ingredient_id
            WHERE ri.recipe_id = %s AND i.ingredient_type = 'ATOMIC'
        """
        
        # 3. Get all FLATTENED materials from COMPOUND ingredients
        # Note: This is complex. It assumes the *first* valid formulation.
        # A more robust solution would be needed for multiple suppliers.
        query_compound = """
            SELECT 
                i_mat.name AS name, 
                (ri.quantity * fm.quantity) AS total_quantity
            FROM 
                RecipeIngredient ri
            JOIN 
                Ingredient i_comp ON ri.ingredient_id = i_comp.ingredient_id
            JOIN 
                Formulation f ON f.ingredient_id = i_comp.ingredient_id
            JOIN 
                FormulationMaterials fm ON fm.formulation_id = f.formulation_id
            JOIN 
                Ingredient i_mat ON fm.material_ingredient_id = i_mat.ingredient_id
            WHERE 
                ri.recipe_id = %s 
                AND i_comp.ingredient_type = 'COMPOUND'
                AND f.valid_from_date <= CURDATE() 
                AND COALESCE(f.valid_to_date, '9999-12-31') >= CURDATE()
        """
        
        cursor.execute(query_atomic, (recipe_id,))
        ingredients = cursor.fetchall()
        
        cursor.execute(query_compound, (recipe_id,))
        ingredients_compound = cursor.fetchall()
        
        # Manually create a new list of dicts to extend
        for item in ingredients_compound:
            ingredients.append({'name': item['name'], 'quantity': item['total_quantity']})

        
        # We need to sum duplicates in Python
        final_list = {}
        for item in ingredients:
            name = item['name']
            # We need to get the key 'quantity' or 'total_quantity'
            qty = item.get('quantity') or item.get('total_quantity', 0)
            if name in final_list:
                final_list[name] += qty
            else:
                final_list[name] = qty
        
        # Sort by quantity descending
        sorted_list = sorted(final_list.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n--- Flattened Ingredient List for Product {product_id} ---")
        print(tabulate(sorted_list, headers=["Ingredient", "Quantity (oz)"], tablefmt="grid"))

    except mysql.connector.Error as err:
        print(f"Error: {err.msg}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def viewer_menu(cursor, db, user_session):
    """(SIMPLE FUNCTIONS) - Menu for Viewer role."""
    while True:
        print("\n--- Viewer Menu ---")
        print("1. Browse Product Types")
        print("2. Generate Ingredient List")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            print("\n--- All Product Types ---")
            try:
                # FIXED: Added 'AS' clauses to match the new pretty_print
                query = """
                    SELECT 
                        p.product_id AS 'ID', 
                        p.name AS 'Product Name', 
                        c.name AS 'Category', 
                        m.name AS 'Manufacturer'
                    FROM Product p
                    JOIN Category c ON p.category_id = c.category_id
                    JOIN Manufacturer m ON p.manufacturer_id = m.manufacturer_id
                    ORDER BY m.name, c.name, p.name
                """
                cursor.execute(query)
                pretty_print_results(cursor) # No headers argument needed
            except mysql.connector.Error as err:
                print(f"Error: {err.msg}")
        elif choice == '2':
            generate_ingredient_list(cursor, db, user_session)
        elif choice == '3':
            break
        else:
            print("Invalid choice.")

# =====================================================================
# --- MAIN EXECUTION ---
# =====================================================================

def main():
    """
    Main function to run the application.
    """
    print("Welcome to the Meal Manufacturer Inventory System")
    db = None
    try:
        # Prompt for password
        db_pass = getpass.getpass("Enter database password (leave blank for no password): ")
        DB_CONFIG['password'] = db_pass
        
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor(dictionary=True) # dictionary=True is very helpful!
        print("Database connection successful.")

        user_session = login(cursor)

        if user_session:
            if user_session['role'] == 'Manufacturer':
                manufacturer_menu(cursor, db, user_session)
            elif user_session['role'] == 'Supplier':
                supplier_menu(cursor, db, user_session)
            elif user_session['role'] == 'Viewer':
                viewer_menu(cursor, db, user_session)

    except mysql.connector.Error as err:
        print(f"\nDatabase Connection Error: {err}")
        print("Please check your MySQL server is running and config is correct.")
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()
            print("\nDatabase connection closed. Goodbye.")

if __name__ == "__main__":
    main()