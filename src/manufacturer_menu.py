#!/usr/bin/env python3
"""
Manufacturer Menu and Functions
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from db_helper import DatabaseHelper

class ManufacturerMenu:
    """Manufacturer role menu and operations"""
    
    def __init__(self, db: DatabaseHelper, user: Dict[str, Any]):
        self.db = db
        self.user = user
        self.manufacturer_id = user['manufacturer_id']
    
    def print_menu(self):
        """Print manufacturer menu"""
        print("=" * 70)
        print("MANUFACTURER MENU")
        print("=" * 70)
        print("  [1] Define/Update Product")
        print("  [2] Define/Update Product BOM (Recipe Plan)")
        print("  [3] Record Ingredient Receipt")
        print("  [4] Create Product Batch")
        print("  [5] Reports")
        print("  [6] Recall/Traceability (Grad)")
        print("  [0] Logout")
        print()
    
    def run(self):
        """Run manufacturer menu loop"""
        while True:
            self.print_menu()
            choice = input("Enter choice: ").strip()
            print()
            
            if choice == '0':
                break
            elif choice == '1':
                self.define_update_product()
            elif choice == '2':
                self.define_update_recipe_plan()
            elif choice == '3':
                self.record_ingredient_receipt()
            elif choice == '4':
                self.create_product_batch()
            elif choice == '5':
                self.reports_menu()
            elif choice == '6':
                self.recall_traceability()
            else:
                print("✗ Invalid choice. Please try again.")
            print()
    
    def define_update_product(self):
        """Create or update a product type"""
        print("=" * 70)
        print("DEFINE/UPDATE PRODUCT")
        print("=" * 70)
        print()
        
        # List existing products for this manufacturer
        query = """
            SELECT p.product_id, p.name, 
                   c.name AS category_name, p.standard_batch_size
            FROM Product p
            JOIN Category c ON p.category_id = c.category_id
            WHERE p.manufacturer_id = %s
            ORDER BY p.product_id
        """
        products = self.db.execute_query(query, (self.manufacturer_id,))
        
        if products:
            print("Existing Products:")
            for p in products:
                print(f"  [{p['product_id']}] {p['name']} ({p['category_name']}) - Batch Size: {p['standard_batch_size']}")
            print()
        
        action = input("Create new product? (y/n): ").strip().lower()
        if action != 'y':
            return
        
        # Get product details
        product_id = input("Product ID (VARCHAR): ").strip()
        if not product_id:
            print("✗ Product ID is required")
            return
        
        product_name = input("Product Name: ").strip()
        if not product_name:
            print("✗ Product name is required")
            return
        
        # List categories
        categories = self.db.execute_query("SELECT category_id, name FROM Category ORDER BY category_id")
        if not categories:
            print("✗ No categories available. Please create categories first.")
            return
        
        print("\nAvailable Categories:")
        for cat in categories:
            print(f"  [{cat['category_id']}] {cat['name']}")
        
        category_id = input("\nCategory ID: ").strip()
        if category_id not in [str(c['category_id']) for c in categories]:
            print("✗ Invalid category ID")
            return
        
        batch_size = input("Standard Batch Size: ").strip()
        if not batch_size.isdigit() or int(batch_size) <= 0:
            print("✗ Batch size must be a positive integer")
            return
        batch_size = int(batch_size)
        
        # Check if product exists
        existing = self.db.execute_query(
            "SELECT product_id FROM Product WHERE product_id = %s",
            (product_id,)
        )
        
        if existing:
            # Update
            query = """
                UPDATE Product 
                SET name = %s, category_id = %s, standard_batch_size = %s
                WHERE product_id = %s AND manufacturer_id = %s
            """
            if self.db.execute_update(query, (product_name, category_id, batch_size, product_id, self.manufacturer_id)):
                print(f"✓ Product {product_id} updated successfully")
        else:
            # Insert
            query = """
                INSERT INTO Product (product_id, name, category_id, manufacturer_id, standard_batch_size)
                VALUES (%s, %s, %s, %s, %s)
            """
            if self.db.execute_update(query, (product_id, product_name, category_id, self.manufacturer_id, batch_size)):
                print(f"✓ Product {product_id} created successfully")
    
    def define_update_recipe_plan(self):
        """Create or update a recipe plan (BOM)"""
        print("=" * 70)
        print("DEFINE/UPDATE RECIPE PLAN")
        print("=" * 70)
        print()
        
        # List products for this manufacturer
        query = """
            SELECT product_id, name 
            FROM Product 
            WHERE manufacturer_id = %s
            ORDER BY product_id
        """
        products = self.db.execute_query(query, (self.manufacturer_id,))
        
        if not products:
            print("✗ No products found. Please create a product first.")
            return
        
        print("Your Products:")
        for p in products:
            print(f"  [{p['product_id']}] {p['name']}")
        
        product_id = input("\nProduct ID: ").strip()
        if product_id not in [str(p['product_id']) for p in products]:
            print("✗ Invalid product ID")
            return
        
        # Get next recipe ID
        next_recipe_id = self.db.get_next_id('Recipe', 'recipe_id')
        
        # Get recipe name
        recipe_name = input("Recipe Name (e.g., v1-standard): ").strip()
        if not recipe_name:
            print("✗ Recipe name is required")
            return
        
        # List available ingredients
        ingredients = self.db.execute_query(
            "SELECT ingredient_id, name, ingredient_type FROM Ingredient ORDER BY ingredient_id"
        )
        
        if not ingredients:
            print("✗ No ingredients available")
            return
        
        print("\nAvailable Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['name']} ({ing['ingredient_type']})")
        
        # Create recipe
        recipe_query = """
            INSERT INTO Recipe (recipe_id, product_id, name, creation_date, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
        """
        if not self.db.execute_update(recipe_query, (next_recipe_id, product_id, recipe_name, datetime.now().date())):
            return
        
        print("\nEnter recipe ingredients (press Enter with empty ingredient ID to finish):")
        recipe_ingredients = []
        unit_of_measure = 'oz'  # Default unit
        
        while True:
            ing_id = input("Ingredient ID: ").strip()
            if not ing_id:
                break
            
            if ing_id not in [str(i['ingredient_id']) for i in ingredients]:
                print("✗ Invalid ingredient ID")
                continue
            
            qty = input("Quantity Required (oz): ").strip()
            try:
                qty = float(qty)
                if qty <= 0:
                    print("✗ Quantity must be positive")
                    continue
            except ValueError:
                print("✗ Invalid quantity")
                continue
            
            recipe_ingredients.append((next_recipe_id, ing_id, qty, unit_of_measure))
            print(f"✓ Added ingredient {ing_id}: {qty} {unit_of_measure}")
        
        if not recipe_ingredients:
            print("✗ Recipe must have at least one ingredient")
            # Delete the recipe
            self.db.execute_update("DELETE FROM Recipe WHERE recipe_id = %s", (next_recipe_id,))
            return
        
        # Insert recipe ingredients
        insert_query = """
            INSERT INTO RecipeIngredient (recipe_id, ingredient_id, quantity, unit_of_measure)
            VALUES (%s, %s, %s, %s)
        """
        if self.db.execute_many(insert_query, recipe_ingredients):
            print(f"\n✓ Recipe {next_recipe_id} ({recipe_name}) created successfully")
            
            # Check for incompatibilities
            self.check_recipe_incompatibilities(next_recipe_id)
    
    def check_recipe_incompatibilities(self, recipe_id: int):
        """Check for do-not-combine conflicts in recipe"""
        query = """
            SELECT DISTINCT dnc.ingredient_a_id, dnc.ingredient_b_id,
                   i1.name AS ing_a_name, i2.name AS ing_b_name
            FROM RecipeIngredient ri1
            JOIN RecipeIngredient ri2 ON ri1.recipe_id = ri2.recipe_id
            JOIN DoNotCombine dnc ON (
                (ri1.ingredient_id = dnc.ingredient_a_id AND ri2.ingredient_id = dnc.ingredient_b_id)
                OR (ri1.ingredient_id = dnc.ingredient_b_id AND ri2.ingredient_id = dnc.ingredient_a_id)
            )
            JOIN Ingredient i1 ON dnc.ingredient_a_id = i1.ingredient_id
            JOIN Ingredient i2 ON dnc.ingredient_b_id = i2.ingredient_id
            WHERE ri1.recipe_id = %s AND ri1.ingredient_id != ri2.ingredient_id
        """
        conflicts = self.db.execute_query(query, (recipe_id,))
        
        if conflicts:
            print("\n⚠ WARNING: Incompatible ingredient pairs detected:")
            for conflict in conflicts:
                print(f"  - {conflict['ing_a_name']} (ID: {conflict['ingredient_a_id']}) "
                      f"cannot be combined with {conflict['ing_b_name']} (ID: {conflict['ingredient_b_id']})")
        else:
            print("\n✓ No incompatibility conflicts detected")
    
    def record_ingredient_receipt(self):
        """Record ingredient receipt (90-day rule)"""
        print("=" * 70)
        print("RECORD INGREDIENT RECEIPT")
        print("=" * 70)
        print()
        print("Note: Expiration date must be at least 90 days from receipt date")
        print()
        
        # List available ingredients
        ingredients = self.db.execute_query(
            "SELECT ingredient_id, name FROM Ingredient ORDER BY ingredient_id"
        )
        if not ingredients:
            print("✗ No ingredients available")
            return
        
        print("Available Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['name']}")
        
        ingredient_id = input("\nIngredient ID: ").strip()
        if ingredient_id not in [str(i['ingredient_id']) for i in ingredients]:
            print("✗ Invalid ingredient ID")
            return
        
        # List suppliers for this ingredient
        suppliers_query = """
            SELECT DISTINCT s.supplier_id, s.name AS supplier_name
            FROM Supplier s
            JOIN IngredientBatch ib ON s.supplier_id = ib.supplier_id
            WHERE ib.ingredient_id = %s
        """
        suppliers = self.db.execute_query(suppliers_query, (ingredient_id,))
        
        # If no existing batches, list all suppliers
        if not suppliers:
            suppliers = self.db.execute_query(
                "SELECT supplier_id, name AS supplier_name FROM Supplier ORDER BY supplier_id"
            )
        
        if not suppliers:
            print("✗ No suppliers found")
            return
        
        print("\nAvailable Suppliers:")
        for sup in suppliers:
            print(f"  [{sup['supplier_id']}] {sup['supplier_name']}")
        
        supplier_id = input("\nSupplier ID: ").strip()
        if supplier_id not in [str(s['supplier_id']) for s in suppliers]:
            print("✗ Invalid supplier ID")
            return
        
        # Get batch details
        quantity = input("Quantity (oz): ").strip()
        try:
            quantity = float(quantity)
            if quantity <= 0:
                print("✗ Quantity must be positive")
                return
        except ValueError:
            print("✗ Invalid quantity")
            return
        
        per_unit_cost = input("Cost per unit: ").strip()
        try:
            per_unit_cost = float(per_unit_cost)
            if per_unit_cost < 0:
                print("✗ Cost cannot be negative")
                return
        except ValueError:
            print("✗ Invalid cost")
            return
        
        intake_date_str = input("Intake Date (YYYY-MM-DD) [today]: ").strip()
        if not intake_date_str:
            intake_date = datetime.now().date()
        else:
            try:
                intake_date = datetime.strptime(intake_date_str, '%Y-%m-%d').date()
            except ValueError:
                print("✗ Invalid date format")
                return
        
        expiration_date_str = input("Expiration Date (YYYY-MM-DD): ").strip()
        try:
            expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
        except ValueError:
            print("✗ Invalid date format")
            return
        
        # Check 90-day rule
        min_expiration = intake_date + timedelta(days=90)
        if expiration_date < min_expiration:
            print(f"✗ Expiration date must be at least 90 days from intake date")
            print(f"  Minimum expiration: {min_expiration}")
            return
        
        # Get supplier batch ID
        supplier_batch_id = input("Supplier Batch ID (for lot number): ").strip()
        if not supplier_batch_id:
            print("✗ Supplier Batch ID is required")
            return
        
        # Check if combination already exists (trigger will create lot_number)
        existing = self.db.execute_query(
            "SELECT lot_number FROM IngredientBatch WHERE ingredient_id = %s AND supplier_id = %s AND supplier_batch_id = %s",
            (ingredient_id, supplier_id, supplier_batch_id)
        )
        if existing:
            print(f"✗ Batch with ingredient_id={ingredient_id}, supplier_id={supplier_id}, supplier_batch_id={supplier_batch_id} already exists")
            return
        
        # Insert ingredient batch (trigger will generate lot_number)
        query = """
            INSERT INTO IngredientBatch 
            (ingredient_id, supplier_id, supplier_batch_id, quantity_on_hand, 
             per_unit_cost, expiration_date, intake_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        if self.db.execute_update(query, (ingredient_id, supplier_id, supplier_batch_id, quantity, per_unit_cost, expiration_date, intake_date)):
            # Get the generated lot number
            lot_result = self.db.execute_query(
                "SELECT lot_number FROM IngredientBatch WHERE ingredient_id = %s AND supplier_id = %s AND supplier_batch_id = %s",
                (ingredient_id, supplier_id, supplier_batch_id)
            )
            lot_number = lot_result[0]['lot_number'] if lot_result else "N/A"
            print(f"✓ Ingredient batch {lot_number} recorded successfully")
            print(f"  Quantity: {quantity} oz")
            print(f"  Cost per unit: ${per_unit_cost:.2f}")
    
    def create_product_batch(self):
        """Create a product batch with lot consumption"""
        print("=" * 70)
        print("CREATE PRODUCT BATCH")
        print("=" * 70)
        print()
        
        # List products
        products = self.db.execute_query(
            "SELECT product_id, name, standard_batch_size FROM Product WHERE manufacturer_id = %s",
            (self.manufacturer_id,)
        )
        
        if not products:
            print("✗ No products found")
            return
        
        print("Your Products:")
        for p in products:
            print(f"  [{p['product_id']}] {p['name']} (Batch Size: {p['standard_batch_size']})")
        
        product_id = input("\nProduct ID: ").strip()
        if product_id not in [str(p['product_id']) for p in products]:
            print("✗ Invalid product ID")
            return
        
        product = next(p for p in products if str(p['product_id']) == product_id)
        batch_size = product['standard_batch_size']
        
        # List active recipes for this product
        recipes = self.db.execute_query(
            """
            SELECT recipe_id, name, creation_date
            FROM Recipe
            WHERE product_id = %s AND is_active = TRUE
            ORDER BY creation_date DESC
            """
        , (product_id,))
        
        if not recipes:
            print("✗ No active recipes found for this product")
            return
        
        print("\nActive Recipes:")
        for recipe in recipes:
            print(f"  [{recipe['recipe_id']}] {recipe['name']} (Created: {recipe['creation_date']})")
        
        recipe_id = input("\nRecipe ID: ").strip()
        if not recipe_id.isdigit() or int(recipe_id) not in [r['recipe_id'] for r in recipes]:
            print("✗ Invalid recipe ID")
            return
        recipe_id = int(recipe_id)
        
        # Get quantity produced
        quantity_str = input(f"Quantity Produced (must be multiple of {batch_size}): ").strip()
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                print("✗ Quantity must be positive")
                return
            if quantity % batch_size != 0:
                print(f"✗ Quantity must be a multiple of {batch_size}")
                return
        except ValueError:
            print("✗ Invalid quantity")
            return
        
        # Get recipe ingredients
        recipe_ingredients = self.db.execute_query(
            """
            SELECT ri.ingredient_id, ri.quantity, i.name AS ingredient_name
            FROM RecipeIngredient ri
            JOIN Ingredient i ON ri.ingredient_id = i.ingredient_id
            WHERE ri.recipe_id = %s
            """
        , (recipe_id,))
        
        if not recipe_ingredients:
            print("✗ Recipe has no ingredients")
            return
        
        print("\nRecipe Ingredients (per unit):")
        for ri in recipe_ingredients:
            print(f"  {ri['ingredient_name']} (ID: {ri['ingredient_id']}): {ri['quantity']} oz")
        
        # Calculate total quantities needed
        total_quantities = {}
        for ri in recipe_ingredients:
            total_quantities[ri['ingredient_id']] = ri['quantity'] * quantity
        
        print(f"\nTotal Quantities Needed (for {quantity} units):")
        for ing_id, qty in total_quantities.items():
            ing_name = next(ri['ingredient_name'] for ri in recipe_ingredients if ri['ingredient_id'] == ing_id)
            print(f"  {ing_name}: {qty} oz")
        
        # Select lots for each ingredient
        print("\nSelect ingredient lots to consume:")
        lot_selections = {}  # {ingredient_id: [(lot_number, quantity_used), ...]}
        
        for ri in recipe_ingredients:
            ing_id = ri['ingredient_id']
            ing_name = ri['ingredient_name']
            needed = total_quantities[ing_id]
            
            print(f"\n{ing_name} (ID: {ing_id}) - Need: {needed} oz")
            
            # Get available lots
            available_lots = self.db.execute_query(
                """
                SELECT lot_number, quantity_on_hand, expiration_date, per_unit_cost
                FROM IngredientBatch
                WHERE ingredient_id = %s 
                  AND quantity_on_hand > 0
                  AND expiration_date > CURDATE()
                ORDER BY expiration_date ASC
                """
            , (ing_id,))
            
            if not available_lots:
                print(f"  ✗ No available lots for {ing_name}")
                return
            
            print("  Available Lots:")
            for lot in available_lots:
                print(f"    [{lot['lot_number']}] {lot['quantity_on_hand']} oz available, "
                      f"expires: {lot['expiration_date']}, cost: ${lot['per_unit_cost']:.2f}/oz")
            
            remaining = needed
            selected_lots = []
            
            while remaining > 0:
                lot_number = input(f"  Enter lot number (need {remaining:.2f} oz more): ").strip()
                if not lot_number:
                    if remaining > 0:
                        print(f"  ✗ Still need {remaining:.2f} oz")
                        return
                    break
                
                lot = next((l for l in available_lots if l['lot_number'] == lot_number), None)
                if not lot:
                    print("  ✗ Invalid lot number")
                    continue
                
                qty_used_str = input(f"  Quantity to use from {lot_number} (max {lot['quantity_on_hand']}): ").strip()
                try:
                    qty_used = float(qty_used_str)
                    if qty_used <= 0:
                        print("  ✗ Quantity must be positive")
                        continue
                    if qty_used > lot['quantity_on_hand']:
                        print(f"  ✗ Cannot use more than {lot['quantity_on_hand']} oz")
                        continue
                    if qty_used > remaining:
                        print(f"  ✗ Only need {remaining:.2f} oz more")
                        continue
                except ValueError:
                    print("  ✗ Invalid quantity")
                    continue
                
                selected_lots.append((lot_number, qty_used))
                remaining -= qty_used
                print(f"  ✓ Selected {qty_used} oz from {lot_number}")
            
            lot_selections[ing_id] = selected_lots
        
        # Get manufacturer batch ID
        manufacturer_batch_id = input("\nManufacturer Batch ID (for lot number): ").strip()
        if not manufacturer_batch_id:
            print("✗ Manufacturer Batch ID is required")
            return
        
        # Check if combination already exists (trigger will create lot_number)
        existing = self.db.execute_query(
            "SELECT lot_number FROM ProductBatch WHERE product_id = %s AND manufacturer_id = %s AND manufacturer_batch_id = %s",
            (product_id, self.manufacturer_id, manufacturer_batch_id)
        )
        if existing:
            print(f"✗ Batch with product_id={product_id}, manufacturer_id={self.manufacturer_id}, manufacturer_batch_id={manufacturer_batch_id} already exists")
            return
        
        # Calculate total cost
        total_cost = 0.0
        for ing_id, lots in lot_selections.items():
            for lot_number, qty_used in lots:
                lot_info = self.db.execute_query(
                    "SELECT per_unit_cost FROM IngredientBatch WHERE lot_number = %s",
                    (lot_number,)
                )
                if lot_info:
                    total_cost += lot_info[0]['per_unit_cost'] * qty_used
        
        total_batch_cost = total_cost
        
        # Get production date
        prod_date_str = input("Production Date (YYYY-MM-DD HH:MM:SS) [today]: ").strip()
        if not prod_date_str:
            prod_date = datetime.now()
        else:
            try:
                # Try with time first
                try:
                    prod_date = datetime.strptime(prod_date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Fall back to date only
                    prod_date = datetime.strptime(prod_date_str, '%Y-%m-%d')
            except ValueError:
                print("✗ Invalid date format")
                return
        
        exp_date_str = input("Expiration Date (YYYY-MM-DD): ").strip()
        try:
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
        except ValueError:
            print("✗ Invalid date format")
            return
        
        # Use transaction to create batch
        try:
            # Insert product batch (trigger will generate lot_number)
            batch_query = """
                INSERT INTO ProductBatch 
                (product_id, manufacturer_id, manufacturer_batch_id, produced_quantity, 
                 production_date, expiration_date, recipe_id_used, total_batch_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            if not self.db.execute_update(batch_query, 
                (product_id, self.manufacturer_id, manufacturer_batch_id, quantity, prod_date, exp_date, recipe_id, total_batch_cost)):
                return
            
            # Get the generated lot number
            lot_result = self.db.execute_query(
                "SELECT lot_number FROM ProductBatch WHERE product_id = %s AND manufacturer_id = %s AND manufacturer_batch_id = %s",
                (product_id, self.manufacturer_id, manufacturer_batch_id)
            )
            if not lot_result:
                print("✗ Error: Could not retrieve generated lot number")
                return
            product_lot_number = lot_result[0]['lot_number']
            
            # Insert batch consumption records and update lot quantities
            for ing_id, lots in lot_selections.items():
                for lot_number, qty_consumed in lots:
                    # Insert consumption record
                    cons_query = """
                        INSERT INTO BatchConsumption (product_lot_number, ingredient_lot_number, quantity_consumed)
                        VALUES (%s, %s, %s)
                    """
                    if not self.db.execute_update(cons_query, (product_lot_number, lot_number, qty_consumed)):
                        return
                    
                    # Update lot quantity
                    update_query = """
                        UPDATE IngredientBatch 
                        SET quantity_on_hand = quantity_on_hand - %s
                        WHERE lot_number = %s
                    """
                    if not self.db.execute_update(update_query, (qty_consumed, lot_number)):
                        return
            
            unit_cost = total_batch_cost / quantity if quantity > 0 else 0
            print(f"\n✓ Product batch {product_lot_number} created successfully")
            print(f"  Quantity: {quantity} units")
            print(f"  Total Cost: ${total_batch_cost:.2f}")
            print(f"  Cost per Unit: ${unit_cost:.2f}")
            
        except Exception as e:
            print(f"✗ Error creating batch: {e}")
            self.db.connection.rollback()
    
    def reports_menu(self):
        """Manufacturer reports menu"""
        while True:
            print("=" * 70)
            print("REPORTS")
            print("=" * 70)
            print("  [1] On-hand by item/lot")
            print("  [2] Nearly out of stock")
            print("  [3] Almost expired ingredient lots")
            print("  [4] Batch Cost Summary")
            print("  [0] Back")
            print()
            
            choice = input("Enter choice: ").strip()
            print()
            
            if choice == '0':
                break
            elif choice == '1':
                self.report_on_hand()
            elif choice == '2':
                self.report_nearly_out_of_stock()
            elif choice == '3':
                self.report_almost_expired()
            elif choice == '4':
                self.report_batch_cost()
            else:
                print("✗ Invalid choice")
            print()
    
    def report_on_hand(self):
        """Report on-hand inventory by item/lot"""
        query = """
            SELECT ib.lot_number, i.name AS ingredient_name, ib.quantity_on_hand, 
                   ib.expiration_date, ib.per_unit_cost
            FROM IngredientBatch ib
            JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
            WHERE ib.quantity_on_hand > 0
            ORDER BY i.name, ib.lot_number
        """
        results = self.db.execute_query(query)
        
        if not results:
            print("No inventory on hand")
            return
        
        print("On-Hand Inventory:")
        print("-" * 70)
        print(f"{'Lot Number':<20} {'Ingredient':<25} {'Quantity':<12} {'Expires':<12} {'Cost/Unit':<10}")
        print("-" * 70)
        for r in results:
            print(f"{r['lot_number']:<20} {r['ingredient_name']:<25} "
                  f"{r['quantity_on_hand']:<12.2f} {str(r['expiration_date']):<12} ${r['per_unit_cost']:<9.2f}")
    
    def report_nearly_out_of_stock(self):
        """Report nearly out of stock items"""
        query = """
            SELECT p.product_id, p.name AS product_name, p.standard_batch_size,
                   SUM(ib.quantity_on_hand) as total_on_hand
            FROM Product p
            JOIN Recipe r ON p.product_id = r.product_id AND r.is_active = TRUE
            JOIN RecipeIngredient ri ON r.recipe_id = ri.recipe_id
            JOIN IngredientBatch ib ON ri.ingredient_id = ib.ingredient_id
            WHERE p.manufacturer_id = %s
            GROUP BY p.product_id, p.name, p.standard_batch_size
            HAVING total_on_hand < p.standard_batch_size
        """
        results = self.db.execute_query(query, (self.manufacturer_id,))
        
        if not results:
            print("No products are nearly out of stock")
            return
        
        print("Nearly Out of Stock Products:")
        print("-" * 70)
        for r in results:
            print(f"Product {r['product_id']}: {r['product_name']}")
            print(f"  Standard Batch Size: {r['standard_batch_size']}")
            print(f"  Total On-Hand: {r['total_on_hand']:.2f} oz")
            print()
    
    def report_almost_expired(self):
        """Report almost expired ingredient lots"""
        days = input("Days threshold (default 30): ").strip()
        days = int(days) if days.isdigit() else 30
        
        query = """
            SELECT ib.lot_number, i.name AS ingredient_name, ib.quantity_on_hand,
                   ib.expiration_date, DATEDIFF(ib.expiration_date, CURDATE()) as days_remaining
            FROM IngredientBatch ib
            JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
            WHERE ib.quantity_on_hand > 0
              AND ib.expiration_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ORDER BY ib.expiration_date ASC
        """
        results = self.db.execute_query(query, (days,))
        
        if not results:
            print(f"No lots expiring within {days} days")
            return
        
        print(f"Almost Expired Lots (within {days} days):")
        print("-" * 70)
        print(f"{'Lot Number':<20} {'Ingredient':<25} {'Quantity':<12} {'Expires':<12} {'Days Left':<10}")
        print("-" * 70)
        for r in results:
            print(f"{r['lot_number']:<20} {r['ingredient_name']:<25} "
                  f"{r['quantity_on_hand']:<12.2f} {str(r['expiration_date']):<12} {r['days_remaining']:<10}")
    
    def report_batch_cost(self):
        """Report batch cost summary"""
        lot_number = input("Product Batch Lot Number: ").strip()
        
        query = """
            SELECT pb.lot_number, p.name AS product_name, pb.produced_quantity,
                   pb.total_batch_cost, pb.production_date
            FROM ProductBatch pb
            JOIN Product p ON pb.product_id = p.product_id
            WHERE pb.lot_number = %s AND p.manufacturer_id = %s
        """
        results = self.db.execute_query(query, (lot_number, self.manufacturer_id))
        
        if not results:
            print("✗ Batch not found or you don't have access")
            return
        
        batch = results[0]
        unit_cost = batch['total_batch_cost'] / batch['produced_quantity'] if batch['produced_quantity'] > 0 else 0
        print(f"\nBatch Cost Summary for {batch['lot_number']}:")
        print("-" * 70)
        print(f"Product: {batch['product_name']}")
        print(f"Quantity Produced: {batch['produced_quantity']} units")
        print(f"Total Cost: ${batch['total_batch_cost']:.2f}")
        print(f"Cost per Unit: ${unit_cost:.2f}")
        print(f"Production Date: {batch['production_date']}")
        
        # Show ingredient consumption
        cons_query = """
            SELECT bc.ingredient_lot_number, i.name AS ingredient_name, bc.quantity_consumed,
                   ib.per_unit_cost, (bc.quantity_consumed * ib.per_unit_cost) as ingredient_cost
            FROM BatchConsumption bc
            JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
            JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
            WHERE bc.product_lot_number = %s
        """
        cons_results = self.db.execute_query(cons_query, (lot_number,))
        
        if cons_results:
            print("\nIngredient Consumption:")
            print("-" * 70)
            for c in cons_results:
                print(f"  {c['ingredient_name']} ({c['ingredient_lot_number']}): "
                      f"{c['quantity_consumed']:.2f} oz @ ${c['per_unit_cost']:.2f}/oz = ${c['ingredient_cost']:.2f}")
    
    def recall_traceability(self):
        """Recall/Traceability (Grad feature)"""
        print("=" * 70)
        print("RECALL/TRACEABILITY")
        print("=" * 70)
        print()
        print("This feature requires the TraceRecall stored procedure.")
        print("Enter ingredient ID or lot number to trace affected product batches.")
        print()
        
        identifier = input("Ingredient ID or Lot Number: ").strip()
        
        # Try to call stored procedure if it exists
        try:
            results = self.db.call_procedure('TraceRecall', (identifier,))
            if results:
                print("\nAffected Product Batches:")
                print("-" * 70)
                for r in results:
                    print(f"Batch: {r.get('batch_number', 'N/A')}, Product: {r.get('product_name', 'N/A')}")
            else:
                print("No affected batches found")
        except:
            print("✗ TraceRecall procedure not available or error occurred")



