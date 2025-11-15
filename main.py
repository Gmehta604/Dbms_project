import mysql.connector
import getpass
import json
import sys
from datetime import date

# --- Database Configuration ---
# NOTE: Your teammates might need to change this if their
# local MySQL user/password is different.
DB_CONFIG = {
    'user': 'root',
    'host': '127.0.0.1',
    'database': 'Meal_Manufacturer'
}

# --- Main Application ---

def login(cursor):
    """
    Handles user login, authenticates against the AppUser table,
    and returns the user's session info.
    """
    print("--- Login ---")
    username = input("Username: ")
    # Use getpass for secure password entry
    password = getpass.getpass("Password: ") 

    # We query for the password (in a real app, this would be a hash)
    query = """
        SELECT role, manufacturer_id, supplier_id 
        FROM AppUser 
        WHERE username = %s AND password_hash = %s
    """
    try:
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        if result:
            role, man_id, sup_id = result
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
    """(Teammate 3's Task) - Simple INSERT"""
    print("\n--- (1) Create & Manage Product Types ---")
    # 1. Get input (name, category_id, standard_batch_size)
    # 2. Run a simple INSERT into the `Product` table.
    #    (Don't forget to include user_session['id'] as the manufacturer_id)
    # 3. Call db.commit()
    print("Function not yet implemented.")
    pass

def create_recipe_plan(cursor, db, user_session):
    """(Teammate 3's Task) - Simple INSERT"""
    print("\n--- (2) Create & Update Recipe Plans (Versioned) ---")
    # 1. Get input (product_id, recipe_name e.g., "v2-low-sodium")
    # 2. INSERT into `Recipe` table.
    # 3. Get the new 'recipe_id' (cursor.lastrowid)
    # 4. Loop:
    #    a. Get input (ingredient_id, quantity, unit)
    #    b. INSERT into `RecipeIngredient` table using the new recipe_id.
    #    c. Ask user "Add another ingredient? (y/n)"
    # 5. Call db.commit()
    print("Function not yet implemented.")
    pass

def create_product_batch(cursor, db, user_session):
    """(Teammate 1's Task) - THIS IS THE BOSS LEVEL FUNCTION"""
    print("\n--- (3) Create Product Batch (Production Posting) ---")
    
    # This is the most complex *Python* task.
    # Your goal is to build the JSON string to pass to the Stored Procedure.
    # Follow the 7-step plan from README.md!
    
    try:
        # --- Step 1: Get Input ---
        product_id = input("Enter Product ID: ") # e.g., '100'
        produced_quantity = int(input("Enter Production Quantity: ")) # e.g., 100
        # ... get other inputs like manufacturer_batch_id, expiration_date

        # --- Step 2: Validate Quantity (Python Check) ---
        cursor.execute("SELECT standard_batch_size FROM Product WHERE product_id = %s", (product_id,))
        sbs = cursor.fetchone()[0]
        if produced_quantity % sbs != 0:
            print(f"Error: Quantity must be a multiple of {sbs}.")
            return

        # --- Step 3: Get Recipe ---
        # (Assuming we use the *active* recipe)
        cursor.execute("SELECT recipe_id FROM Recipe WHERE product_id = %s AND is_active = 1", (product_id,))
        recipe_id_used = cursor.fetchone()[0]
        
        cursor.execute("SELECT ingredient_id, quantity FROM RecipeIngredient WHERE recipe_id = %s", (recipe_id_used,))
        recipe_ingredients = cursor.fetchall() # e.g., [('106', 6.0), ('201', 0.2)]

        # --- Step 4 & 5: Calculate Totals & Run FEFO Logic ---
        print("Calculating inventory requirements...")
        consumption_plan = [] # This will become our JSON
        
        for ing_id, qty_per_unit in recipe_ingredients:
            total_needed = qty_per_unit * produced_quantity
            print(f"Need {total_needed} oz of ingredient {ing_id}...")
            
            # This is the FEFO (First-Expired, First-Out) query
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
            
            # --- This is the core FEFO loop ---
            for lot_number, lot_qty in available_lots:
                if total_needed <= 0:
                    break # We have enough of this ingredient
                
                consume_qty = min(lot_qty, total_needed)
                consumption_plan.append({"lot": lot_number, "qty": float(consume_qty)})
                total_needed -= consume_qty
            
            if total_needed > 0:
                print(f"*** CRITICAL ERROR: Not enough stock for ingredient {ing_id}! ***")
                print(f"Still need {total_needed} oz.")
                print("Batch creation cancelled.")
                return

        # --- Step 6: Build the JSON ---
        json_string = json.dumps(consumption_plan)
        print("\nConsumption Plan (JSON):")
        print(json_string)
        
        if input("Do you want to proceed with this batch? (y/n): ") != 'y':
            print("Batch creation cancelled.")
            return

        # --- Step 7: CALL the Stored Procedure ---
        print("Calling Record_Production_Batch...")
        args = (
            product_id,
            user_session['id'],
            input("Enter new Manufacturer Batch ID (e.g., B0902): "),
            produced_quantity,
            input("Enter Expiration Date (YYYY-MM-DD): "),
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

    pass

def run_manufacturer_reports(cursor, user_session):
    """(Teammate 2's Task) - Run the 5 Required Queries"""
    print("\n--- (5) Run Reports ---")
    
    # Create a sub-menu for the 5 queries
    print("1. Ingredients of last 'Steak Dinner' batch (MFG001)")
    print("2. Suppliers and spending (MFG002)")
    print("3. Unit cost for lot '100-MFG001-B0901'")
    print("4. Conflicting ingredients for lot '100-MFG001-B0901'")
    print("5. Manufacturers not supplied by 'James Miller' (21)")
    
    choice = input("Select a report (1-5): ")
    
    if choice == '1':
        # --- Query 1 ---
        # The SQL is already written in project_plan.md
        # 1. Define the SQL query string
        # 2. cursor.execute(query)
        # 3. results = cursor.fetchall()
        # 4. Pretty-print the results
        print("Running Query 1...")
        query1 = """
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
            LIMIT 1;
        """
        cursor.execute(query1)
        for row in cursor.fetchall():
            print(row)

    elif choice == '2':
        # --- Query 2 ---
        print("Running Query 2...")
        # (Paste SQL from project_plan.md here)
    
    # ... Add elif for 3, 4, and 5 ...
    
    else:
        print("Invalid choice.")
    pass

def manufacturer_menu(cursor, db, user_session):
    """Main menu loop for the Manufacturer role."""
    while True:
        print("\n--- Manufacturer Menu ---")
        print("1. Create/Update Product Type")
        print("2. Create/Update Recipe Plan")
        print("3. Create Product Batch (Production Posting)")
        print("4. (View Reports - see 5)")
        print("5. Run Reports (Required Queries)")
        print("6. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            create_product_type(cursor, db, user_session)
        elif choice == '2':
            create_recipe_plan(cursor, db, user_session)
        elif choice == '3':
            create_product_batch(cursor, db, user_session)
        elif choice == '5':
            run_manufacturer_reports(cursor, user_session)
        elif choice == '6':
            break
        else:
            print("Invalid choice.")

# =====================================================================
# --- SUPPLIER MENU ---
# =====================================================================

def create_supplier_batch(cursor, db, user_session):
    """(Teammate 3's Task) - Simple INSERT with 90-day check"""
    print("\n--- (3) Create Ingredient Batch (Lot Intake) ---")
    # 1. Get input: ingredient_id, supplier_batch_id, quantity, cost, expiration_date
    # 2. Get today's date: intake_date = date.today()
    # 3. Python Check (90-day rule):
    #    if (expiration_date - intake_date).days < 90:
    #       print("Error: Expiration date must be at least 90 days out.")
    #       return
    # 4. Run INSERT into `IngredientBatch` table.
    #    (The triggers will do all the work!)
    # 5. Call db.commit()
    print("Function not yet implemented.")
    pass

def supplier_menu(cursor, db, user_session):
    """(Teammate 3's Task)"""
    while True:
        print("\n--- Supplier Menu ---")
        print("1. Manage Ingredients Supplied")
        print("2. Define/Update Ingredient (Formulation)")
        print("3. Create Ingredient Batch (Lot Intake)")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            # (UI for INSERT/UPDATE on Formulation table)
            print("Function not yet implemented.")
        elif choice == '2':
            # (UI for INSERT/UPDATE on FormulationMaterials)
            print("Function not yet implemented.")
        elif choice == '3.':
            create_supplier_batch(cursor, db, user_session)
        elif choice == '4':
            break
        else:
            print("Invalid choice.")
    pass

# =====================================================================
# --- VIEWER MENU ---
# =====================================================================

def generate_ingredient_list(cursor, user_session):
    """(Teammate 3's Task) - Complex SELECT"""
    print("\n--- (1) Generate Ingredient List ---")
    # This is a complex SELECT query.
    # 1. Get product_id from user.
    # 2. Find the *active* recipe_id.
    # 3. Get all ingredients from `RecipeIngredient`.
    # 4. For each ingredient, if it's 'COMPOUND':
    #    a. Find its *active* formulation.
    #    b. Find its `FormulationMaterials`.
    # 5. Combine this "flattened" list, SUM quantities, and
    #    ORDER BY quantity DESC.
    print("Function not yet implemented.")
    pass

def viewer_menu(cursor, db, user_session):
    """(Teammate 3's Task)"""
    while True:
        print("\n--- Viewer Menu ---")
        print("1. Browse Product Types")
        print("2. Generate Ingredient List")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            # (Simple SELECT on Product, Category, Manufacturer)
            print("Function not yet implemented.")
        elif choice == '2':
            generate_ingredient_list(cursor, user_session)
        elif choice == '3':
            break
        else:
            print("Invalid choice.")
    pass

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
        db_pass = getpass.getpass("Enter database password: ")
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