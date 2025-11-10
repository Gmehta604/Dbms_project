#!/usr/bin/env python3
"""
CSC540 Project 1: Inventory Management System
Menu-driven application for Prepared/Frozen Meals Manufacturer
"""

import mysql.connector
from mysql.connector import Error
import sys
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict

class InventoryApp:
    def __init__(self, host='localhost',port=3306, database='csc_540', 
                 user='root', password = 'Gaura@01062002'):
        """Initialize database connection"""
        self.connection = None
        self.cursor = None
        self.current_user_id = None
        self.current_role = None
        self.current_manufacturer_id = None
        self.current_supplier_id = None
        
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port = port,
                database=database,
                user=user,
                password=password
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("Successfully connected to database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            sys.exit(1)
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Database connection closed")
    
    def login(self):
        """User login and role selection"""
        print("\n" + "="*60)
        print("INVENTORY MANAGEMENT SYSTEM")
        print("="*60)
        print("\nSelect Role:")
        print("1. Manufacturer")
        print("2. Supplier")
        print("3. General (Viewer)")
        print("4. View Queries")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            return False
        
        if choice == '4':
            self.view_queries()
            return False
        
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        role_map = {'1': 'Manufacturer', '2': 'Supplier', '3': 'Viewer'}
        expected_role = role_map.get(choice)
        
        if not expected_role:
            print("Invalid choice")
            return False
        
        # Verify credentials
        query = "SELECT user_id, role FROM USERS WHERE username = %s AND password = %s AND role = %s"
        self.cursor.execute(query, (username, password, expected_role))
        user = self.cursor.fetchone()
        
        if user:
            self.current_user_id = user['user_id']
            self.current_role = user['role']
            
            # Get manufacturer or supplier ID
            if self.current_role == 'Manufacturer':
                self.cursor.execute("SELECT manufacturer_id FROM MANUFACTURERS WHERE user_id = %s", 
                                  (self.current_user_id,))
                mfg = self.cursor.fetchone()
                if mfg:
                    self.current_manufacturer_id = mfg['manufacturer_id']
            
            elif self.current_role == 'Supplier':
                self.cursor.execute("SELECT supplier_id FROM SUPPLIERS WHERE user_id = %s", 
                                  (self.current_user_id,))
                supp = self.cursor.fetchone()
                if supp:
                    self.current_supplier_id = supp['supplier_id']
            
            print(f"\nLogged in as {username} ({self.current_role})")
            return True
        else:
            print("Invalid credentials or role mismatch")
            return False
    
    def manufacturer_menu(self):
        """Manufacturer menu"""
        while True:
            print("\n" + "="*60)
            print("MANUFACTURER MENU")
            print("="*60)
            print("1. Products")
            print("   a. Create/Update Product")
            print("   b. Recipe Plans")
            print("2. Production")
            print("   a. Create Product Batch")
            print("3. Inventory")
            print("   a. Record Ingredient Receipt")
            print("4. Reports")
            print("   a. On-hand by item/lot")
            print("   b. Nearly-out-of-stock")
            print("   c. Almost-expired ingredient lots")
            print("   d. Batch Cost Summary")
            print("5. Recall & Traceability")
            print("0. Logout")
            
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == '0':
                break
            elif choice == '1a':
                self.create_update_product()
            elif choice == '1b':
                self.manage_recipe_plans()
            elif choice == '2a':
                self.create_product_batch()
            elif choice == '3a':
                self.record_ingredient_receipt()
            elif choice == '4a':
                self.report_onhand()
            elif choice == '4b':
                self.report_nearly_out_of_stock()
            elif choice == '4c':
                self.report_almost_expired()
            elif choice == '4d':
                self.report_batch_cost()
            elif choice == '5':
                self.trace_recall()
            else:
                print("Invalid choice")
    
    def supplier_menu(self):
        """Supplier menu"""
        while True:
            print("\n" + "="*60)
            print("SUPPLIER MENU")
            print("="*60)
            print("1. Manage Ingredients Supplied")
            print("2. Ingredients")
            print("   a. Create/Update Ingredient")
            print("   b. Do-Not-Combine List")
            print("3. Inventory")
            print("   a. Receive Ingredient Batch")
            print("0. Logout")
            
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == '0':
                break
            elif choice == '1':
                self.manage_supplier_ingredients()
            elif choice == '2a':
                self.create_update_ingredient()
            elif choice == '2b':
                self.manage_do_not_combine()
            elif choice == '3a':
                self.receive_ingredient_batch()
            else:
                print("Invalid choice")
    
    def viewer_menu(self):
        """General viewer menu"""
        while True:
            print("\n" + "="*60)
            print("VIEWER MENU")
            print("="*60)
            print("1. Browse Products")
            print("2. Product Ingredient List")
            print("3. Compare Products for Incompatibilities")
            print("0. Logout")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.browse_products()
            elif choice == '2':
                self.generate_ingredient_list()
            elif choice == '3':
                self.compare_products()
            else:
                print("Invalid choice")
    
    # ============================================================================
    # MANUFACTURER FUNCTIONS
    # ============================================================================
    
    def create_update_product(self):
        """Create or update a product"""
        print("\n--- Create/Update Product ---")
        product_name = input("Product name: ").strip()
        
        # Check if product exists
        query = "SELECT product_id FROM PRODUCTS WHERE product_name = %s AND manufacturer_id = %s"
        self.cursor.execute(query, (product_name, self.current_manufacturer_id))
        existing = self.cursor.fetchone()
        
        # Get categories
        self.cursor.execute("SELECT category_id, category_name FROM CATEGORIES")
        categories = self.cursor.fetchall()
        print("\nCategories:")
        for cat in categories:
            print(f"  {cat['category_id']}. {cat['category_name']}")
        
        category_id = int(input("Category ID: "))
        standard_batch_size = int(input("Standard batch size (units): "))
        
        if existing:
            # Update
            query = """UPDATE PRODUCTS SET category_id = %s, standard_batch_size = %s 
                      WHERE product_id = %s"""
            self.cursor.execute(query, (category_id, standard_batch_size, existing['product_id']))
            print("Product updated successfully")
        else:
            # Create
            query = """INSERT INTO PRODUCTS (manufacturer_id, category_id, product_name, 
                      standard_batch_size, created_date) VALUES (%s, %s, %s, %s, %s)"""
            self.cursor.execute(query, (self.current_manufacturer_id, category_id, product_name, 
                                       standard_batch_size, date.today()))
            print("Product created successfully")
        
        self.connection.commit()
    
    def manage_recipe_plans(self):
        """Manage recipe plans for products"""
        print("\n--- Recipe Plans ---")
        
        # List products
        query = "SELECT product_id, product_name FROM PRODUCTS WHERE manufacturer_id = %s"
        self.cursor.execute(query, (self.current_manufacturer_id,))
        products = self.cursor.fetchall()
        
        print("\nYour Products:")
        for p in products:
            print(f"  {p['product_id']}. {p['product_name']}")
        
        product_id = int(input("\nSelect product ID: "))
        
        # Get latest version
        query = """SELECT MAX(version_number) as max_version FROM RECIPE_PLANS 
                  WHERE product_id = %s"""
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        new_version = (result['max_version'] or 0) + 1
        
        print(f"\nCreating version {new_version}")
        
        # Create new plan
        query = """INSERT INTO RECIPE_PLANS (product_id, version_number, created_date, is_active) 
                  VALUES (%s, %s, %s, TRUE)"""
        self.cursor.execute(query, (product_id, new_version, date.today()))
        plan_id = self.cursor.lastrowid
        
        # Deactivate old plans
        query = "UPDATE RECIPE_PLANS SET is_active = FALSE WHERE product_id = %s AND plan_id != %s"
        self.cursor.execute(query, (product_id, plan_id))
        
        # Add ingredients
        print("\nAdd ingredients (enter 0 to finish):")
        while True:
            self.cursor.execute("SELECT ingredient_id, ingredient_name FROM INGREDIENTS ORDER BY ingredient_name")
            ingredients = self.cursor.fetchall()
            print("\nAvailable Ingredients:")
            for ing in ingredients:
                print(f"  {ing['ingredient_id']}. {ing['ingredient_name']}")
            
            ingredient_id = int(input("Ingredient ID (0 to finish): "))
            if ingredient_id == 0:
                break
            
            quantity = float(input("Quantity required (oz per unit): "))
            
            query = """INSERT INTO RECIPE_INGREDIENTS (plan_id, ingredient_id, quantity_required) 
                      VALUES (%s, %s, %s)"""
            self.cursor.execute(query, (plan_id, ingredient_id, quantity))
        
        self.connection.commit()
        print("Recipe plan created successfully")
    
    def create_product_batch(self):
        """Create a product batch using stored procedure"""
        print("\n--- Create Product Batch ---")
        
        # List products
        query = "SELECT product_id, product_name FROM PRODUCTS WHERE manufacturer_id = %s"
        self.cursor.execute(query, (self.current_manufacturer_id,))
        products = self.cursor.fetchall()
        
        print("\nYour Products:")
        for p in products:
            print(f"  {p['product_id']}. {p['product_name']}")
        
        product_id = int(input("\nProduct ID: "))
        
        # Get active recipe plan
        query = """SELECT plan_id, version_number FROM RECIPE_PLANS 
                  WHERE product_id = %s AND is_active = TRUE"""
        self.cursor.execute(query, (product_id,))
        plan = self.cursor.fetchone()
        
        if not plan:
            print("No active recipe plan found")
            return
        
        print(f"Using recipe plan version {plan['version_number']}")
        
        # Get standard batch size
        query = "SELECT standard_batch_size FROM PRODUCTS WHERE product_id = %s"
        self.cursor.execute(query, (product_id,))
        product = self.cursor.fetchone()
        standard_size = product['standard_batch_size']
        
        quantity = int(input(f"Quantity to produce (must be multiple of {standard_size}): "))
        
        if quantity % standard_size != 0:
            print(f"Quantity must be a multiple of {standard_size}")
            return
        
        production_date = input("Production date (YYYY-MM-DD) [today]: ").strip()
        if not production_date:
            production_date = date.today()
        else:
            production_date = datetime.strptime(production_date, '%Y-%m-%d').date()
        
        expiration_date = input("Expiration date (YYYY-MM-DD): ").strip()
        expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
        
        # Call stored procedure
        args = (product_id, plan['plan_id'], quantity, production_date, expiration_date,
                0, '', 0.0, 0.0, '', '')
        
        result = self.cursor.callproc('sp_record_production_batch', args)
        
        # Get output parameters
        self.cursor.execute("SELECT @_sp_record_production_batch_5, @_sp_record_production_batch_6")
        status_result = self.cursor.fetchone()
        
        if status_result['@_sp_record_production_batch_5'] == 'SUCCESS':
            print(f"\nBatch created successfully!")
            print(f"Batch ID: {result[5]}")
            print(f"Batch Number: {result[6]}")
            print(f"Total Cost: ${result[7]:.2f}")
            print(f"Cost per Unit: ${result[8]:.2f}")
        else:
            print(f"\nError: {status_result['@_sp_record_production_batch_6']}")
    
    def record_ingredient_receipt(self):
        """Record ingredient receipt (90-day rule enforced by trigger)"""
        print("\n--- Record Ingredient Receipt ---")
        
        ingredient_id = int(input("Ingredient ID: "))
        quantity = float(input("Quantity (oz): "))
        cost_per_unit = float(input("Cost per unit: "))
        expiration_date = input("Expiration date (YYYY-MM-DD): ").strip()
        expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
        received_date = date.today()
        
        # Get supplier (assuming current manufacturer receives from a supplier)
        # In real app, would select supplier
        supplier_id = int(input("Supplier ID: "))
        
        # Insert (trigger will compute lot number and validate expiration)
        query = """INSERT INTO INGREDIENT_BATCHES 
                  (ingredient_id, supplier_id, quantity_on_hand, cost_per_unit, 
                   expiration_date, received_date) 
                  VALUES (%s, %s, %s, %s, %s, %s)"""
        
        try:
            self.cursor.execute(query, (ingredient_id, supplier_id, quantity, 
                                       cost_per_unit, expiration_date, received_date))
            self.connection.commit()
            print("Ingredient batch recorded successfully")
        except Error as e:
            print(f"Error: {e}")
            self.connection.rollback()
    
    def report_onhand(self):
        """Report on-hand inventory by item/lot"""
        print("\n--- On-Hand Inventory Report ---")
        
        query = """SELECT ib.ingredient_batch_id, i.ingredient_name, ib.lot_number, 
                  ib.quantity_on_hand, ib.expiration_date, s.supplier_name
                  FROM INGREDIENT_BATCHES ib
                  INNER JOIN INGREDIENTS i ON ib.ingredient_id = i.ingredient_id
                  INNER JOIN SUPPLIERS s ON ib.supplier_id = s.supplier_id
                  WHERE ib.quantity_on_hand > 0
                  ORDER BY i.ingredient_name, ib.expiration_date"""
        
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        print(f"\n{'Ingredient':<30} {'Lot Number':<20} {'Qty (oz)':<12} {'Expiration':<12} {'Supplier':<20}")
        print("-" * 100)
        for row in results:
            print(f"{row['ingredient_name']:<30} {row['lot_number']:<20} "
                  f"{row['quantity_on_hand']:<12.2f} {str(row['expiration_date']):<12} "
                  f"{row['supplier_name']:<20}")
    
    def report_nearly_out_of_stock(self):
        """Report nearly-out-of-stock items"""
        print("\n--- Nearly Out of Stock Report ---")
        
        query = """SELECT i.ingredient_name, 
                  SUM(ib.quantity_on_hand) as total_on_hand,
                  p.standard_batch_size
                  FROM INGREDIENT_BATCHES ib
                  INNER JOIN INGREDIENTS i ON ib.ingredient_id = i.ingredient_id
                  INNER JOIN RECIPE_INGREDIENTS ri ON i.ingredient_id = ri.ingredient_id
                  INNER JOIN RECIPE_PLANS rp ON ri.plan_id = rp.plan_id
                  INNER JOIN PRODUCTS p ON rp.product_id = p.product_id
                  WHERE p.manufacturer_id = %s AND rp.is_active = TRUE
                  GROUP BY i.ingredient_id, i.ingredient_name, p.standard_batch_size
                  HAVING total_on_hand < p.standard_batch_size"""
        
        self.cursor.execute(query, (self.current_manufacturer_id,))
        results = self.cursor.fetchall()
        
        if results:
            print(f"\n{'Ingredient':<30} {'On Hand (oz)':<15} {'Standard Batch':<15}")
            print("-" * 60)
            for row in results:
                print(f"{row['ingredient_name']:<30} {row['total_on_hand']:<15.2f} "
                      f"{row['standard_batch_size']:<15}")
        else:
            print("\nNo items nearly out of stock")
    
    def report_almost_expired(self):
        """Report almost-expired ingredient lots (within 10 days)"""
        print("\n--- Almost Expired Report (within 10 days) ---")
        
        threshold_date = date.today() + timedelta(days=10)
        
        query = """SELECT i.ingredient_name, ib.lot_number, ib.quantity_on_hand, 
                  ib.expiration_date, DATEDIFF(ib.expiration_date, CURDATE()) as days_remaining
                  FROM INGREDIENT_BATCHES ib
                  INNER JOIN INGREDIENTS i ON ib.ingredient_id = i.ingredient_id
                  WHERE ib.expiration_date <= %s AND ib.expiration_date >= CURDATE()
                    AND ib.quantity_on_hand > 0
                  ORDER BY ib.expiration_date"""
        
        self.cursor.execute(query, (threshold_date,))
        results = self.cursor.fetchall()
        
        if results:
            print(f"\n{'Ingredient':<30} {'Lot Number':<20} {'Qty (oz)':<12} "
                  f"{'Expiration':<12} {'Days Left':<10}")
            print("-" * 90)
            for row in results:
                print(f"{row['ingredient_name']:<30} {row['lot_number']:<20} "
                      f"{row['quantity_on_hand']:<12.2f} {str(row['expiration_date']):<12} "
                      f"{row['days_remaining']:<10}")
        else:
            print("\nNo items expiring within 10 days")
    
    def report_batch_cost(self):
        """Report batch cost summary"""
        print("\n--- Batch Cost Summary ---")
        
        batch_number = input("Enter batch number: ").strip()
        
        query = """SELECT pb.batch_number, p.product_name, pb.quantity_produced, 
                  pb.total_cost, pb.cost_per_unit, pb.production_date
                  FROM PRODUCT_BATCHES pb
                  INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
                  WHERE pb.batch_number = %s AND p.manufacturer_id = %s"""
        
        self.cursor.execute(query, (batch_number, self.current_manufacturer_id))
        batch = self.cursor.fetchone()
        
        if batch:
            print(f"\nBatch: {batch['batch_number']}")
            print(f"Product: {batch['product_name']}")
            print(f"Quantity Produced: {batch['quantity_produced']} units")
            print(f"Total Cost: ${batch['total_cost']:.2f}")
            print(f"Cost per Unit: ${batch['cost_per_unit']:.2f}")
            print(f"Production Date: {batch['production_date']}")
        else:
            print("Batch not found")
    
    def trace_recall(self):
        """Trace recall for ingredient or lot"""
        print("\n--- Recall Traceability ---")
        print("1. By Ingredient ID")
        print("2. By Lot Number")
        
        choice = input("Choice: ").strip()
        
        ingredient_id = None
        lot_number = None
        days_window = 20
        
        if choice == '1':
            ingredient_id = int(input("Ingredient ID: "))
        elif choice == '2':
            lot_number = input("Lot Number: ").strip()
        else:
            print("Invalid choice")
            return
        
        # Call stored procedure
        args = (ingredient_id, lot_number, days_window, '')
        result = self.cursor.callproc('sp_trace_recall', args)
        
        print(f"\nAffected batches: {result[3]}")
    
    # ============================================================================
    # SUPPLIER FUNCTIONS
    # ============================================================================
    
    def manage_supplier_ingredients(self):
        """Manage which ingredients supplier can provide"""
        print("\n--- Manage Ingredients Supplied ---")
        
        self.cursor.execute("SELECT ingredient_id, ingredient_name FROM INGREDIENTS ORDER BY ingredient_name")
        ingredients = self.cursor.fetchall()
        
        print("\nAvailable Ingredients:")
        for ing in ingredients:
            print(f"  {ing['ingredient_id']}. {ing['ingredient_name']}")
        
        ingredient_id = int(input("\nIngredient ID to add/remove: "))
        is_active = input("Active? (y/n): ").strip().lower() == 'y'
        
        query = """INSERT INTO SUPPLIER_INGREDIENTS (supplier_id, ingredient_id, is_active) 
                  VALUES (%s, %s, %s)
                  ON DUPLICATE KEY UPDATE is_active = %s"""
        self.cursor.execute(query, (self.current_supplier_id, ingredient_id, is_active, is_active))
        self.connection.commit()
        print("Updated successfully")
    
    def create_update_ingredient(self):
        """Create or update ingredient definition"""
        print("\n--- Create/Update Ingredient ---")
        
        ingredient_name = input("Ingredient name: ").strip()
        ingredient_type = input("Type (Atomic/Compound): ").strip()
        
        if ingredient_type not in ['Atomic', 'Compound']:
            print("Invalid type")
            return
        
        # Check if exists
        query = "SELECT ingredient_id FROM INGREDIENTS WHERE ingredient_name = %s"
        self.cursor.execute(query, (ingredient_name,))
        existing = self.cursor.fetchone()
        
        if existing:
            ingredient_id = existing['ingredient_id']
            print(f"Updating ingredient ID {ingredient_id}")
        else:
            query = """INSERT INTO INGREDIENTS (ingredient_name, ingredient_type, unit_of_measure) 
                      VALUES (%s, %s, 'oz')"""
            self.cursor.execute(query, (ingredient_name, ingredient_type))
            ingredient_id = self.cursor.lastrowid
            print(f"Created ingredient ID {ingredient_id}")
        
        # If compound, add materials
        if ingredient_type == 'Compound':
            print("\nAdd materials (child ingredients):")
            while True:
                self.cursor.execute("SELECT ingredient_id, ingredient_name FROM INGREDIENTS WHERE ingredient_id != %s", 
                                  (ingredient_id,))
                ingredients = self.cursor.fetchall()
                print("\nAvailable Ingredients:")
                for ing in ingredients:
                    print(f"  {ing['ingredient_id']}. {ing['ingredient_name']}")
                
                child_id = int(input("Child ingredient ID (0 to finish): "))
                if child_id == 0:
                    break
                
                quantity = float(input("Quantity required (oz): "))
                
                query = """INSERT INTO INGREDIENT_COMPOSITIONS 
                          (parent_ingredient_id, child_ingredient_id, quantity_required) 
                          VALUES (%s, %s, %s)
                          ON DUPLICATE KEY UPDATE quantity_required = %s"""
                self.cursor.execute(query, (ingredient_id, child_id, quantity, quantity))
        
        self.connection.commit()
        print("Ingredient saved successfully")
    
    def manage_do_not_combine(self):
        """Manage do-not-combine list"""
        print("\n--- Do-Not-Combine List ---")
        
        self.cursor.execute("SELECT ingredient_id, ingredient_name FROM INGREDIENTS ORDER BY ingredient_name")
        ingredients = self.cursor.fetchall()
        
        print("\nIngredients:")
        for ing in ingredients:
            print(f"  {ing['ingredient_id']}. {ing['ingredient_name']}")
        
        ing1_id = int(input("\nFirst ingredient ID: "))
        ing2_id = int(input("Second ingredient ID: "))
        reason = input("Reason: ").strip()
        
        query = """INSERT INTO DO_NOT_COMBINE (ingredient1_id, ingredient2_id, reason, created_date) 
                  VALUES (%s, %s, %s, %s)"""
        self.cursor.execute(query, (ing1_id, ing2_id, reason, date.today()))
        self.connection.commit()
        print("Rule added successfully")
    
    def receive_ingredient_batch(self):
        """Receive ingredient batch (supplier creates their own inventory)"""
        print("\n--- Receive Ingredient Batch ---")
        
        # List ingredients this supplier can provide
        query = """SELECT i.ingredient_id, i.ingredient_name 
                  FROM INGREDIENTS i
                  INNER JOIN SUPPLIER_INGREDIENTS si ON i.ingredient_id = si.ingredient_id
                  WHERE si.supplier_id = %s AND si.is_active = TRUE"""
        self.cursor.execute(query, (self.current_supplier_id,))
        ingredients = self.cursor.fetchall()
        
        print("\nIngredients you supply:")
        for ing in ingredients:
            print(f"  {ing['ingredient_id']}. {ing['ingredient_name']}")
        
        ingredient_id = int(input("\nIngredient ID: "))
        
        # Verify supplier can provide this ingredient
        query = """SELECT 1 FROM SUPPLIER_INGREDIENTS 
                  WHERE supplier_id = %s AND ingredient_id = %s AND is_active = TRUE"""
        self.cursor.execute(query, (self.current_supplier_id, ingredient_id))
        if not self.cursor.fetchone():
            print("You cannot supply this ingredient")
            return
        
        quantity = float(input("Quantity (oz): "))
        cost_per_unit = float(input("Cost per unit: "))
        expiration_date = input("Expiration date (YYYY-MM-DD): ").strip()
        expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
        received_date = date.today()
        
        # Insert (trigger will compute lot number and validate expiration)
        query = """INSERT INTO INGREDIENT_BATCHES 
                  (ingredient_id, supplier_id, quantity_on_hand, cost_per_unit, 
                   expiration_date, received_date) 
                  VALUES (%s, %s, %s, %s, %s, %s)"""
        
        try:
            self.cursor.execute(query, (ingredient_id, self.current_supplier_id, quantity, 
                                       cost_per_unit, expiration_date, received_date))
            self.connection.commit()
            
            # Get the lot number that was generated
            self.cursor.execute("SELECT lot_number FROM INGREDIENT_BATCHES WHERE ingredient_batch_id = LAST_INSERT_ID()")
            result = self.cursor.fetchone()
            print(f"Ingredient batch recorded successfully. Lot number: {result['lot_number']}")
        except Error as e:
            print(f"Error: {e}")
            self.connection.rollback()
    
    # ============================================================================
    # VIEWER FUNCTIONS
    # ============================================================================
    
    def browse_products(self):
        """Browse available products"""
        print("\n--- Browse Products ---")
        
        query = """SELECT p.product_id, p.product_name, c.category_name, m.manufacturer_name
                  FROM PRODUCTS p
                  INNER JOIN CATEGORIES c ON p.category_id = c.category_id
                  INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
                  ORDER BY m.manufacturer_name, c.category_name, p.product_name"""
        
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        print(f"\n{'Product':<30} {'Category':<20} {'Manufacturer':<20}")
        print("-" * 70)
        for row in results:
            print(f"{row['product_name']:<30} {row['category_name']:<20} {row['manufacturer_name']:<20}")
    
    def generate_ingredient_list(self):
        """Generate ingredient list for a product (using view)"""
        print("\n--- Product Ingredient List ---")
        
        product_id = int(input("Product ID: "))
        
        query = """SELECT final_ingredient_name, total_quantity_contribution
                  FROM vw_flattened_product_bom
                  WHERE product_id = %s
                  ORDER BY total_quantity_contribution DESC"""
        
        self.cursor.execute(query, (product_id,))
        results = self.cursor.fetchall()
        
        if results:
            print(f"\n{'Ingredient':<30} {'Quantity (oz per unit)':<25}")
            print("-" * 55)
            for row in results:
                print(f"{row['final_ingredient_name']:<30} {row['total_quantity_contribution']:<25.2f}")
        else:
            print("Product not found or no ingredients")
    
    def compare_products(self):
        """Compare two products for incompatibilities"""
        print("\n--- Compare Products ---")
        
        product1_id = int(input("First product ID: "))
        product2_id = int(input("Second product ID: "))
        
        # Get all ingredients from both products (flattened)
        query = """SELECT DISTINCT final_ingredient_id
                  FROM vw_flattened_product_bom
                  WHERE product_id IN (%s, %s)"""
        
        self.cursor.execute(query, (product1_id, product2_id))
        ingredient_ids = [row['final_ingredient_id'] for row in self.cursor.fetchall()]
        
        if not ingredient_ids:
            print("No ingredients found")
            return
        
        # Check for conflicts
        placeholders = ','.join(['%s'] * len(ingredient_ids))
        query = f"""SELECT dnc.ingredient1_id, i1.ingredient_name as ing1_name,
                   dnc.ingredient2_id, i2.ingredient_name as ing2_name, dnc.reason
                   FROM DO_NOT_COMBINE dnc
                   INNER JOIN INGREDIENTS i1 ON dnc.ingredient1_id = i1.ingredient_id
                   INNER JOIN INGREDIENTS i2 ON dnc.ingredient2_id = i2.ingredient_id
                   WHERE dnc.ingredient1_id IN ({placeholders})
                     AND dnc.ingredient2_id IN ({placeholders})"""
        
        self.cursor.execute(query, ingredient_ids + ingredient_ids)
        conflicts = self.cursor.fetchall()
        
        if conflicts:
            print("\nIncompatible pairs found:")
            for conflict in conflicts:
                print(f"  {conflict['ing1_name']} <-> {conflict['ing2_name']}: {conflict['reason']}")
        else:
            print("\nNo incompatibilities found")
    
    def view_queries(self):
        """View the 5 required queries"""
        print("\n" + "="*60)
        print("REQUIRED QUERIES")
        print("="*60)
        print("\n1. Ingredients and lot numbers of last Steak Dinner batch by MFG001")
        print("2. Suppliers and total spending for MFG002")
        print("3. Unit cost for product lot 100-MFG001-B0901")
        print("4. Conflicting ingredients for product lot 100-MFG001-B0901")
        print("5. Manufacturers NOT supplied by James Miller (21)")
        print("0. Back")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            query = """SELECT i.ingredient_id, i.ingredient_name, ib.lot_number AS ingredient_lot_number, 
                     bc.quantity_used
                     FROM PRODUCT_BATCHES pb
                     INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
                     INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
                     INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
                     INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
                     INNER JOIN INGREDIENTS i ON ib.ingredient_id = i.ingredient_id
                     WHERE p.product_id = 100 AND m.manufacturer_id = 1
                     AND pb.production_date = (
                         SELECT MAX(pb2.production_date)
                         FROM PRODUCT_BATCHES pb2
                         INNER JOIN PRODUCTS p2 ON pb2.product_id = p2.product_id
                         WHERE p2.product_id = 100 AND p2.manufacturer_id = 1
                     )
                     ORDER BY i.ingredient_name"""
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            print(f"\n{'Ingredient':<30} {'Lot Number':<25} {'Quantity Used':<15}")
            print("-" * 70)
            for row in results:
                print(f"{row['ingredient_name']:<30} {row['ingredient_lot_number']:<25} {row['quantity_used']:<15.2f}")
        
        elif choice == '2':
            query = """SELECT s.supplier_id, s.supplier_name, 
                     SUM(bc.quantity_used * ib.cost_per_unit) AS total_amount_spent
                     FROM MANUFACTURERS m
                     INNER JOIN PRODUCTS p ON m.manufacturer_id = p.manufacturer_id
                     INNER JOIN PRODUCT_BATCHES pb ON p.product_id = pb.product_id
                     INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
                     INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
                     INNER JOIN SUPPLIERS s ON ib.supplier_id = s.supplier_id
                     WHERE m.manufacturer_id = 2
                     GROUP BY s.supplier_id, s.supplier_name
                     ORDER BY total_amount_spent DESC"""
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            print(f"\n{'Supplier':<30} {'Total Amount Spent':<20}")
            print("-" * 50)
            for row in results:
                print(f"{row['supplier_name']:<30} ${row['total_amount_spent']:<19.2f}")
        
        elif choice == '3':
            query = """SELECT pb.batch_number, pb.cost_per_unit, pb.total_cost, 
                     pb.quantity_produced, p.product_name, m.manufacturer_name
                     FROM PRODUCT_BATCHES pb
                     INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
                     INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
                     WHERE CONCAT(pb.product_id, '-', m.manufacturer_name, '-B', 
                           SUBSTRING_INDEX(pb.batch_number, 'B', -1)) = '100-MFG001-B0901'
                        OR pb.batch_number = '100-1-B0901'"""
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            if result:
                print(f"\nBatch: {result['batch_number']}")
                print(f"Product: {result['product_name']}")
                print(f"Unit Cost: ${result['cost_per_unit']:.2f}")
                print(f"Total Cost: ${result['total_cost']:.2f}")
                print(f"Quantity: {result['quantity_produced']} units")
            else:
                print("Batch not found")
        
        elif choice == '4':
            # This is a complex query - using the CTE approach
            query = """WITH product_ingredients AS (
                SELECT DISTINCT ib.ingredient_id
                FROM PRODUCT_BATCHES pb
                INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
                INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
                INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
                INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
                WHERE (CONCAT(pb.product_id, '-', m.manufacturer_name, '-B', 
                      SUBSTRING_INDEX(pb.batch_number, 'B', -1)) = '100-MFG001-B0901'
                   OR pb.batch_number = '100-1-B0901')
                UNION
                SELECT DISTINCT ic.child_ingredient_id
                FROM PRODUCT_BATCHES pb
                INNER JOIN PRODUCTS p ON pb.product_id = p.product_id
                INNER JOIN MANUFACTURERS m ON p.manufacturer_id = m.manufacturer_id
                INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
                INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
                INNER JOIN INGREDIENT_COMPOSITIONS ic ON ib.ingredient_id = ic.parent_ingredient_id
                WHERE (CONCAT(pb.product_id, '-', m.manufacturer_name, '-B', 
                      SUBSTRING_INDEX(pb.batch_number, 'B', -1)) = '100-MFG001-B0901'
                   OR pb.batch_number = '100-1-B0901')
            )
            SELECT DISTINCT i.ingredient_id, i.ingredient_name, dnc.reason AS conflict_reason
            FROM DO_NOT_COMBINE dnc
            INNER JOIN INGREDIENTS i ON (
                (dnc.ingredient1_id = i.ingredient_id AND dnc.ingredient2_id IN (SELECT ingredient_id FROM product_ingredients))
                OR (dnc.ingredient2_id = i.ingredient_id AND dnc.ingredient1_id IN (SELECT ingredient_id FROM product_ingredients))
            )
            WHERE dnc.ingredient1_id IN (SELECT ingredient_id FROM product_ingredients)
               OR dnc.ingredient2_id IN (SELECT ingredient_id FROM product_ingredients)
            ORDER BY i.ingredient_name"""
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            if results:
                print(f"\n{'Ingredient':<30} {'Conflict Reason':<50}")
                print("-" * 80)
                for row in results:
                    print(f"{row['ingredient_name']:<30} {row['conflict_reason']:<50}")
            else:
                print("No conflicting ingredients found")
        
        elif choice == '5':
            query = """SELECT m.manufacturer_id, m.manufacturer_name
                     FROM MANUFACTURERS m
                     WHERE m.manufacturer_id NOT IN (
                         SELECT DISTINCT p.manufacturer_id
                         FROM PRODUCTS p
                         INNER JOIN PRODUCT_BATCHES pb ON p.product_id = pb.product_id
                         INNER JOIN BATCH_CONSUMPTION bc ON pb.product_batch_id = bc.product_batch_id
                         INNER JOIN INGREDIENT_BATCHES ib ON bc.ingredient_batch_id = ib.ingredient_batch_id
                         WHERE ib.supplier_id = 21
                     )
                     ORDER BY m.manufacturer_name"""
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            if results:
                print(f"\n{'Manufacturer ID':<20} {'Manufacturer Name':<30}")
                print("-" * 50)
                for row in results:
                    print(f"{row['manufacturer_id']:<20} {row['manufacturer_name']:<30}")
            else:
                print("All manufacturers have been supplied by James Miller")
        
        input("\nPress Enter to continue...")
    
    def run(self):
        """Main application loop"""
        try:
            while True:
                if not self.login():
                    break
                
                if self.current_role == 'Manufacturer':
                    self.manufacturer_menu()
                elif self.current_role == 'Supplier':
                    self.supplier_menu()
                elif self.current_role == 'Viewer':
                    self.viewer_menu()
                
                # Reset session
                self.current_user_id = None
                self.current_role = None
                self.current_manufacturer_id = None
                self.current_supplier_id = None
        
        finally:
            self.close()


def main():
    """Main entry point"""
    # Database connection parameters
    # Update these with your actual database credentials
    app = InventoryApp(
        host='localhost',
        port=3306,
        database='csc_540',
        user='root',
        password='Gaurav$01062002'  # Set your password here
    )
    
    app.run()


if __name__ == '__main__':
    main()


