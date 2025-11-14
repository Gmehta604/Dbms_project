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
            SELECT p.product_id, p.product_number, p.product_name, 
                   c.category_name, p.standard_batch_size
            FROM Products p
            JOIN Categories c ON p.category_id = c.category_id
            WHERE p.manufacturer_id = %s
            ORDER BY p.product_id
        """
        products = self.db.execute_query(query, (self.manufacturer_id,))
        
        if products:
            print("Existing Products:")
            for p in products:
                print(f"  [{p['product_id']}] {p['product_name']} ({p['category_name']}) - Batch Size: {p['standard_batch_size']}")
            print()
        
        action = input("Create new product? (y/n): ").strip().lower()
        if action != 'y':
            return
        
        # Get product details
        product_id = input("Product ID (integer): ").strip()
        if not product_id.isdigit():
            print("✗ Product ID must be an integer")
            return
        product_id = int(product_id)
        
        product_number = input("Product Number (optional): ").strip() or None
        product_name = input("Product Name: ").strip()
        if not product_name:
            print("✗ Product name is required")
            return
        
        # List categories
        categories = self.db.execute_query("SELECT category_id, category_name FROM Categories ORDER BY category_id")
        if not categories:
            print("✗ No categories available. Please create categories first.")
            return
        
        print("\nAvailable Categories:")
        for cat in categories:
            print(f"  [{cat['category_id']}] {cat['category_name']}")
        
        category_id = input("\nCategory ID: ").strip()
        if not category_id.isdigit() or int(category_id) not in [c['category_id'] for c in categories]:
            print("✗ Invalid category ID")
            return
        category_id = int(category_id)
        
        batch_size = input("Standard Batch Size: ").strip()
        if not batch_size.isdigit() or int(batch_size) <= 0:
            print("✗ Batch size must be a positive integer")
            return
        batch_size = int(batch_size)
        
        # Check if product exists
        existing = self.db.execute_query(
            "SELECT product_id FROM Products WHERE product_id = %s",
            (product_id,)
        )
        
        if existing:
            # Update
            query = """
                UPDATE Products 
                SET product_number = %s, product_name = %s, 
                    category_id = %s, standard_batch_size = %s
                WHERE product_id = %s AND manufacturer_id = %s
            """
            if self.db.execute_update(query, (product_number, product_name, category_id, batch_size, product_id, self.manufacturer_id)):
                print(f"✓ Product {product_id} updated successfully")
        else:
            # Insert
            query = """
                INSERT INTO Products (product_id, product_number, manufacturer_id, 
                                    category_id, product_name, standard_batch_size, created_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            if self.db.execute_update(query, (product_id, product_number, self.manufacturer_id, category_id, product_name, batch_size, datetime.now().date())):
                print(f"✓ Product {product_id} created successfully")
    
    def define_update_recipe_plan(self):
        """Create or update a recipe plan (BOM)"""
        print("=" * 70)
        print("DEFINE/UPDATE RECIPE PLAN")
        print("=" * 70)
        print()
        
        # List products for this manufacturer
        query = """
            SELECT product_id, product_name 
            FROM Products 
            WHERE manufacturer_id = %s
            ORDER BY product_id
        """
        products = self.db.execute_query(query, (self.manufacturer_id,))
        
        if not products:
            print("✗ No products found. Please create a product first.")
            return
        
        print("Your Products:")
        for p in products:
            print(f"  [{p['product_id']}] {p['product_name']}")
        
        product_id = input("\nProduct ID: ").strip()
        if not product_id.isdigit() or int(product_id) not in [p['product_id'] for p in products]:
            print("✗ Invalid product ID")
            return
        product_id = int(product_id)
        
        # Get next plan ID and version
        next_plan_id = self.db.get_next_id('Recipe_Plans', 'plan_id')
        
        # Get latest version for this product
        version_query = """
            SELECT MAX(version_number) as max_version 
            FROM Recipe_Plans 
            WHERE product_id = %s
        """
        version_result = self.db.execute_query(version_query, (product_id,))
        next_version = (version_result[0]['max_version'] or 0) + 1
        
        print(f"\nCreating new recipe plan version {next_version} (Plan ID: {next_plan_id})")
        
        # List available ingredients
        ingredients = self.db.execute_query(
            "SELECT ingredient_id, ingredient_name, ingredient_type FROM Ingredients ORDER BY ingredient_id"
        )
        
        if not ingredients:
            print("✗ No ingredients available")
            return
        
        print("\nAvailable Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']} ({ing['ingredient_type']})")
        
        # Create recipe plan
        plan_query = """
            INSERT INTO Recipe_Plans (plan_id, product_id, version_number, created_date, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
        """
        if not self.db.execute_update(plan_query, (next_plan_id, product_id, next_version, datetime.now().date())):
            return
        
        print("\nEnter recipe ingredients (press Enter with empty ingredient ID to finish):")
        recipe_ingredients = []
        
        while True:
            ing_id = input("Ingredient ID: ").strip()
            if not ing_id:
                break
            
            if not ing_id.isdigit() or int(ing_id) not in [i['ingredient_id'] for i in ingredients]:
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
            
            recipe_ingredients.append((next_plan_id, int(ing_id), qty))
            print(f"✓ Added ingredient {ing_id}: {qty} oz")
        
        if not recipe_ingredients:
            print("✗ Recipe plan must have at least one ingredient")
            # Delete the plan
            self.db.execute_update("DELETE FROM Recipe_Plans WHERE plan_id = %s", (next_plan_id,))
            return
        
        # Insert recipe ingredients
        insert_query = """
            INSERT INTO Recipe_Ingredients (plan_id, ingredient_id, quantity_required)
            VALUES (%s, %s, %s)
        """
        if self.db.execute_many(insert_query, recipe_ingredients):
            print(f"\n✓ Recipe plan {next_plan_id} (version {next_version}) created successfully")
            
            # Check for incompatibilities
            self.check_recipe_incompatibilities(next_plan_id)
    
    def check_recipe_incompatibilities(self, plan_id: int):
        """Check for do-not-combine conflicts in recipe plan"""
        query = """
            SELECT DISTINCT dnc.ingredient1_id, dnc.ingredient2_id,
                   i1.ingredient_name as ing1_name, i2.ingredient_name as ing2_name
            FROM Recipe_Ingredients ri1
            JOIN Recipe_Ingredients ri2 ON ri1.plan_id = ri2.plan_id
            JOIN Do_Not_Combine dnc ON (
                (ri1.ingredient_id = dnc.ingredient1_id AND ri2.ingredient_id = dnc.ingredient2_id)
                OR (ri1.ingredient_id = dnc.ingredient2_id AND ri2.ingredient_id = dnc.ingredient1_id)
            )
            JOIN Ingredients i1 ON dnc.ingredient1_id = i1.ingredient_id
            JOIN Ingredients i2 ON dnc.ingredient2_id = i2.ingredient_id
            WHERE ri1.plan_id = %s AND ri1.ingredient_id != ri2.ingredient_id
        """
        conflicts = self.db.execute_query(query, (plan_id,))
        
        if conflicts:
            print("\n⚠ WARNING: Incompatible ingredient pairs detected:")
            for conflict in conflicts:
                print(f"  - {conflict['ing1_name']} (ID: {conflict['ingredient1_id']}) "
                      f"cannot be combined with {conflict['ing2_name']} (ID: {conflict['ingredient2_id']})")
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
            "SELECT ingredient_id, ingredient_name FROM Ingredients ORDER BY ingredient_id"
        )
        if not ingredients:
            print("✗ No ingredients available")
            return
        
        print("Available Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']}")
        
        ingredient_id = input("\nIngredient ID: ").strip()
        if not ingredient_id.isdigit() or int(ingredient_id) not in [i['ingredient_id'] for i in ingredients]:
            print("✗ Invalid ingredient ID")
            return
        ingredient_id = int(ingredient_id)
        
        # List suppliers for this ingredient
        suppliers_query = """
            SELECT s.supplier_id, s.supplier_name
            FROM Suppliers s
            JOIN Supplier_Ingredients si ON s.supplier_id = si.supplier_id
            WHERE si.ingredient_id = %s AND si.is_active = TRUE
        """
        suppliers = self.db.execute_query(suppliers_query, (ingredient_id,))
        
        if not suppliers:
            print("✗ No active suppliers found for this ingredient")
            return
        
        print("\nAvailable Suppliers:")
        for sup in suppliers:
            print(f"  [{sup['supplier_id']}] {sup['supplier_name']}")
        
        supplier_id = input("\nSupplier ID: ").strip()
        if not supplier_id.isdigit() or int(supplier_id) not in [s['supplier_id'] for s in suppliers]:
            print("✗ Invalid supplier ID")
            return
        supplier_id = int(supplier_id)
        
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
        
        cost_per_unit = input("Cost per unit: ").strip()
        try:
            cost_per_unit = float(cost_per_unit)
            if cost_per_unit < 0:
                print("✗ Cost cannot be negative")
                return
        except ValueError:
            print("✗ Invalid cost")
            return
        
        received_date_str = input("Received Date (YYYY-MM-DD) [today]: ").strip()
        if not received_date_str:
            received_date = datetime.now().date()
        else:
            try:
                received_date = datetime.strptime(received_date_str, '%Y-%m-%d').date()
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
        min_expiration = received_date + timedelta(days=90)
        if expiration_date < min_expiration:
            print(f"✗ Expiration date must be at least 90 days from receipt date")
            print(f"  Minimum expiration: {min_expiration}")
            return
        
        # Generate lot number
        batch_id = input("Batch ID (for lot number): ").strip()
        if not batch_id:
            print("✗ Batch ID is required")
            return
        
        lot_number = f"{ingredient_id}-{supplier_id}-{batch_id}"
        
        # Check if lot number already exists
        existing = self.db.execute_query(
            "SELECT lot_number FROM Ingredient_Batches WHERE lot_number = %s",
            (lot_number,)
        )
        if existing:
            print(f"✗ Lot number {lot_number} already exists")
            return
        
        # Insert ingredient batch
        query = """
            INSERT INTO Ingredient_Batches 
            (lot_number, ingredient_id, supplier_id, version_id, quantity_on_hand, 
             cost_per_unit, expiration_date, received_date)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, %s)
        """
        if self.db.execute_update(query, (lot_number, ingredient_id, supplier_id, quantity, cost_per_unit, expiration_date, received_date)):
            print(f"✓ Ingredient batch {lot_number} recorded successfully")
            print(f"  Quantity: {quantity} oz")
            print(f"  Cost per unit: ${cost_per_unit:.2f}")
    
    def create_product_batch(self):
        """Create a product batch with lot consumption"""
        print("=" * 70)
        print("CREATE PRODUCT BATCH")
        print("=" * 70)
        print()
        
        # List products
        products = self.db.execute_query(
            "SELECT product_id, product_name, standard_batch_size FROM Products WHERE manufacturer_id = %s",
            (self.manufacturer_id,)
        )
        
        if not products:
            print("✗ No products found")
            return
        
        print("Your Products:")
        for p in products:
            print(f"  [{p['product_id']}] {p['product_name']} (Batch Size: {p['standard_batch_size']})")
        
        product_id = input("\nProduct ID: ").strip()
        if not product_id.isdigit() or int(product_id) not in [p['product_id'] for p in products]:
            print("✗ Invalid product ID")
            return
        product_id = int(product_id)
        
        product = next(p for p in products if p['product_id'] == product_id)
        batch_size = product['standard_batch_size']
        
        # List active recipe plans for this product
        plans = self.db.execute_query(
            """
            SELECT plan_id, version_number, created_date
            FROM Recipe_Plans
            WHERE product_id = %s AND is_active = TRUE
            ORDER BY version_number DESC
            """
        , (product_id,))
        
        if not plans:
            print("✗ No active recipe plans found for this product")
            return
        
        print("\nActive Recipe Plans:")
        for plan in plans:
            print(f"  [{plan['plan_id']}] Version {plan['version_number']} (Created: {plan['created_date']})")
        
        plan_id = input("\nRecipe Plan ID: ").strip()
        if not plan_id.isdigit() or int(plan_id) not in [p['plan_id'] for p in plans]:
            print("✗ Invalid plan ID")
            return
        plan_id = int(plan_id)
        
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
            SELECT ri.ingredient_id, ri.quantity_required, i.ingredient_name
            FROM Recipe_Ingredients ri
            JOIN Ingredients i ON ri.ingredient_id = i.ingredient_id
            WHERE ri.plan_id = %s
            """
        , (plan_id,))
        
        if not recipe_ingredients:
            print("✗ Recipe plan has no ingredients")
            return
        
        print("\nRecipe Ingredients (per unit):")
        for ri in recipe_ingredients:
            print(f"  {ri['ingredient_name']} (ID: {ri['ingredient_id']}): {ri['quantity_required']} oz")
        
        # Calculate total quantities needed
        total_quantities = {}
        for ri in recipe_ingredients:
            total_quantities[ri['ingredient_id']] = ri['quantity_required'] * quantity
        
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
                SELECT lot_number, quantity_on_hand, expiration_date, cost_per_unit
                FROM Ingredient_Batches
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
                      f"expires: {lot['expiration_date']}, cost: ${lot['cost_per_unit']:.2f}/oz")
            
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
        
        # Generate product batch number
        batch_id = input("\nBatch ID (for batch number): ").strip()
        if not batch_id:
            print("✗ Batch ID is required")
            return
        
        batch_number = f"{product_id}-{self.manufacturer_id}-{batch_id}"
        
        # Check if batch number exists
        existing = self.db.execute_query(
            "SELECT batch_number FROM Product_Batches WHERE batch_number = %s",
            (batch_number,)
        )
        if existing:
            print(f"✗ Batch number {batch_number} already exists")
            return
        
        # Calculate total cost
        total_cost = 0.0
        for ing_id, lots in lot_selections.items():
            for lot_number, qty_used in lots:
                lot_info = self.db.execute_query(
                    "SELECT cost_per_unit FROM Ingredient_Batches WHERE lot_number = %s",
                    (lot_number,)
                )
                if lot_info:
                    total_cost += lot_info[0]['cost_per_unit'] * qty_used
        
        cost_per_unit = total_cost / quantity if quantity > 0 else 0
        
        # Get production date
        prod_date_str = input("Production Date (YYYY-MM-DD) [today]: ").strip()
        if not prod_date_str:
            prod_date = datetime.now().date()
        else:
            try:
                prod_date = datetime.strptime(prod_date_str, '%Y-%m-%d').date()
            except ValueError:
                print("✗ Invalid date format")
                return
        
        exp_date_str = input("Expiration Date (YYYY-MM-DD): ").strip()
        try:
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
        except ValueError:
            print("✗ Invalid date format")
            return
        
        # Use stored procedure to create batch (if exists) or do it manually
        # For now, do it manually with transaction
        try:
            # Insert product batch
            batch_query = """
                INSERT INTO Product_Batches 
                (batch_number, product_id, plan_id, quantity_produced, total_cost, 
                 cost_per_unit, production_date, expiration_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            if not self.db.execute_update(batch_query, 
                (batch_number, product_id, plan_id, quantity, total_cost, cost_per_unit, prod_date, exp_date)):
                return
            
            # Insert batch consumption records and update lot quantities
            for ing_id, lots in lot_selections.items():
                for lot_number, qty_used in lots:
                    # Insert consumption record
                    cons_query = """
                        INSERT INTO Batch_Consumption (product_batch_number, ingredient_lot_number, quantity_used)
                        VALUES (%s, %s, %s)
                    """
                    if not self.db.execute_update(cons_query, (batch_number, lot_number, qty_used)):
                        return
                    
                    # Update lot quantity
                    update_query = """
                        UPDATE Ingredient_Batches 
                        SET quantity_on_hand = quantity_on_hand - %s
                        WHERE lot_number = %s
                    """
                    if not self.db.execute_update(update_query, (qty_used, lot_number)):
                        return
            
            print(f"\n✓ Product batch {batch_number} created successfully")
            print(f"  Quantity: {quantity} units")
            print(f"  Total Cost: ${total_cost:.2f}")
            print(f"  Cost per Unit: ${cost_per_unit:.2f}")
            
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
            SELECT ib.lot_number, i.ingredient_name, ib.quantity_on_hand, 
                   ib.expiration_date, ib.cost_per_unit
            FROM Ingredient_Batches ib
            JOIN Ingredients i ON ib.ingredient_id = i.ingredient_id
            WHERE ib.quantity_on_hand > 0
            ORDER BY i.ingredient_name, ib.lot_number
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
                  f"{r['quantity_on_hand']:<12.2f} {str(r['expiration_date']):<12} ${r['cost_per_unit']:<9.2f}")
    
    def report_nearly_out_of_stock(self):
        """Report nearly out of stock items"""
        query = """
            SELECT p.product_id, p.product_name, p.standard_batch_size,
                   SUM(ib.quantity_on_hand) as total_on_hand
            FROM Products p
            JOIN Recipe_Plans rp ON p.product_id = rp.product_id AND rp.is_active = TRUE
            JOIN Recipe_Ingredients ri ON rp.plan_id = ri.plan_id
            JOIN Ingredient_Batches ib ON ri.ingredient_id = ib.ingredient_id
            WHERE p.manufacturer_id = %s
            GROUP BY p.product_id, p.product_name, p.standard_batch_size
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
            SELECT ib.lot_number, i.ingredient_name, ib.quantity_on_hand,
                   ib.expiration_date, DATEDIFF(ib.expiration_date, CURDATE()) as days_remaining
            FROM Ingredient_Batches ib
            JOIN Ingredients i ON ib.ingredient_id = i.ingredient_id
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
        batch_number = input("Product Batch Number: ").strip()
        
        query = """
            SELECT pb.batch_number, p.product_name, pb.quantity_produced,
                   pb.total_cost, pb.cost_per_unit, pb.production_date
            FROM Product_Batches pb
            JOIN Products p ON pb.product_id = p.product_id
            WHERE pb.batch_number = %s AND p.manufacturer_id = %s
        """
        results = self.db.execute_query(query, (batch_number, self.manufacturer_id))
        
        if not results:
            print("✗ Batch not found or you don't have access")
            return
        
        batch = results[0]
        print(f"\nBatch Cost Summary for {batch['batch_number']}:")
        print("-" * 70)
        print(f"Product: {batch['product_name']}")
        print(f"Quantity Produced: {batch['quantity_produced']} units")
        print(f"Total Cost: ${batch['total_cost']:.2f}")
        print(f"Cost per Unit: ${batch['cost_per_unit']:.2f}")
        print(f"Production Date: {batch['production_date']}")
        
        # Show ingredient consumption
        cons_query = """
            SELECT bc.ingredient_lot_number, i.ingredient_name, bc.quantity_used,
                   ib.cost_per_unit, (bc.quantity_used * ib.cost_per_unit) as ingredient_cost
            FROM Batch_Consumption bc
            JOIN Ingredient_Batches ib ON bc.ingredient_lot_number = ib.lot_number
            JOIN Ingredients i ON ib.ingredient_id = i.ingredient_id
            WHERE bc.product_batch_number = %s
        """
        cons_results = self.db.execute_query(cons_query, (batch_number,))
        
        if cons_results:
            print("\nIngredient Consumption:")
            print("-" * 70)
            for c in cons_results:
                print(f"  {c['ingredient_name']} ({c['ingredient_lot_number']}): "
                      f"{c['quantity_used']:.2f} oz @ ${c['cost_per_unit']:.2f}/oz = ${c['ingredient_cost']:.2f}")
    
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


