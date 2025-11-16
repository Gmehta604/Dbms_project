#!/usr/bin/env python3
"""
Supplier Menu and Functions
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from db_helper import DatabaseHelper

class SupplierMenu:
    """Supplier role menu and operations"""
    
    def __init__(self, db: DatabaseHelper, user: Dict[str, Any]):
        self.db = db
        self.user = user
        self.supplier_id = user['supplier_id']
    
    def print_menu(self):
        """Print supplier menu"""
        print("=" * 70)
        print("SUPPLIER MENU")
        print("=" * 70)
        print("  [1] Manage Ingredients Supplied")
        print("  [2] Define/Update Ingredient (Atomic or Compound)")
        print("  [3] Maintain Do-Not-Combine List (Grad)")
        print("  [4] Maintain Formulations")
        print("  [5] Create Ingredient Batch (Lot Intake)")
        print("  [0] Logout")
        print()
    
    def run(self):
        """Run supplier menu loop"""
        while True:
            self.print_menu()
            choice = input("Enter choice: ").strip()
            print()
            
            if choice == '0':
                break
            elif choice == '1':
                self.manage_ingredients_supplied()
            elif choice == '2':
                self.define_update_ingredient()
            elif choice == '3':
                self.maintain_do_not_combine()
            elif choice == '4':
                self.maintain_formulations()
            elif choice == '5':
                self.create_ingredient_batch()
            else:
                print("✗ Invalid choice. Please try again.")
            print()
    
    def manage_ingredients_supplied(self):
        """Manage which ingredients this supplier provides"""
        print("=" * 70)
        print("MANAGE INGREDIENTS SUPPLIED")
        print("=" * 70)
        print()
        print("Note: Suppliers provide ingredients through Formulations and Ingredient Batches.")
        print("Use 'Maintain Formulations' and 'Create Ingredient Batch' to manage supplied ingredients.")
        print()
        
        # Show ingredients this supplier has formulations or batches for
        query = """
            SELECT DISTINCT i.ingredient_id, i.name AS ingredient_name
            FROM Ingredient i
            WHERE i.ingredient_id IN (
                SELECT DISTINCT f.ingredient_id FROM Formulation f WHERE f.supplier_id = %s
                UNION
                SELECT DISTINCT ib.ingredient_id FROM IngredientBatch ib WHERE ib.supplier_id = %s
            )
            ORDER BY i.ingredient_id
        """
        supplied = self.db.execute_query(query, (self.supplier_id, self.supplier_id))
        
        print("Ingredients You Currently Supply:")
        if supplied:
            for ing in supplied:
                print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']}")
        else:
            print("  (none)")
        print()
        
        # List all ingredients
        all_ingredients = self.db.execute_query(
            "SELECT ingredient_id, name FROM Ingredient ORDER BY ingredient_id"
        )
        
        print("All Available Ingredients:")
        for ing in all_ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['name']}")
        print()
        
        print("To supply an ingredient:")
        print("  1. Create a Formulation for it (Menu option 4)")
        print("  2. Or create an Ingredient Batch directly (Menu option 5)")
    
    def define_update_ingredient(self):
        """Define or update an ingredient (atomic or compound)"""
        print("=" * 70)
        print("DEFINE/UPDATE INGREDIENT")
        print("=" * 70)
        print()
        
        # List existing ingredients
        ingredients = self.db.execute_query(
            "SELECT ingredient_id, name, ingredient_type FROM Ingredient ORDER BY ingredient_id"
        )
        
        print("Existing Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['name']} ({ing['ingredient_type']})")
        print()
        
        action = input("Create new ingredient? (y/n): ").strip().lower()
        if action != 'y':
            # Update existing
            ing_id = input("Ingredient ID to update: ").strip()
            if ing_id not in [str(i['ingredient_id']) for i in ingredients]:
                print("✗ Invalid ingredient ID")
                return
            
            existing = self.db.execute_query(
                "SELECT * FROM Ingredient WHERE ingredient_id = %s",
                (ing_id,)
            )
            if not existing:
                print("✗ Ingredient not found")
                return
            
            ing = existing[0]
            print(f"\nCurrent: {ing['name']} ({ing['ingredient_type']})")
            
            name = input(f"Name [{ing['name']}]: ").strip() or ing['name']
            ing_type = input(f"Type (ATOMIC/COMPOUND) [{ing['ingredient_type']}]: ").strip().upper() or ing['ingredient_type']
            if ing_type not in ['ATOMIC', 'COMPOUND']:
                print("✗ Type must be ATOMIC or COMPOUND")
                return
            
            query = """
                UPDATE Ingredient 
                SET name = %s, ingredient_type = %s
                WHERE ingredient_id = %s
            """
            if self.db.execute_update(query, (name, ing_type, ing_id)):
                print(f"✓ Ingredient {ing_id} updated")
            
            # Note: Compound ingredients use Formulations, not separate composition table
            if ing_type == 'COMPOUND':
                print("Note: Compound ingredients should use Formulations with FormulationMaterials.")
            
            return
        
        # Create new ingredient
        ingredient_id = input("Ingredient ID (VARCHAR): ").strip()
        if not ingredient_id:
            print("✗ Ingredient ID is required")
            return
        
        # Check if exists
        existing = self.db.execute_query(
            "SELECT ingredient_id FROM Ingredient WHERE ingredient_id = %s",
            (ingredient_id,)
        )
        if existing:
            print("✗ Ingredient ID already exists")
            return
        
        ingredient_name = input("Ingredient Name: ").strip()
        if not ingredient_name:
            print("✗ Ingredient name is required")
            return
        
        ingredient_type = input("Type (ATOMIC/COMPOUND): ").strip().upper()
        if ingredient_type not in ['ATOMIC', 'COMPOUND']:
            print("✗ Type must be ATOMIC or COMPOUND")
            return
        
        # Insert ingredient
        query = """
            INSERT INTO Ingredient (ingredient_id, name, ingredient_type)
            VALUES (%s, %s, %s)
        """
        if not self.db.execute_update(query, (ingredient_id, ingredient_name, ingredient_type)):
            return
        
        print(f"✓ Ingredient {ingredient_id} created")
        
        # Note: Compound ingredients use Formulations
        if ingredient_type == 'COMPOUND':
            print("Note: Create a Formulation for this compound ingredient with its atomic materials.")
    
    # Note: Compound ingredient composition is handled through Formulations and FormulationMaterials
    # This method is no longer needed - removed
    
    def maintain_do_not_combine(self):
        """Maintain do-not-combine list (Grad feature)"""
        print("=" * 70)
        print("MAINTAIN DO-NOT-COMBINE LIST")
        print("=" * 70)
        print()
        
        # List current conflicts (global - not supplier-specific)
        query = """
            SELECT dnc.ingredient_a_id, dnc.ingredient_b_id,
                   i1.name AS ing_a_name, i2.name AS ing_b_name
            FROM DoNotCombine dnc
            JOIN Ingredient i1 ON dnc.ingredient_a_id = i1.ingredient_id
            JOIN Ingredient i2 ON dnc.ingredient_b_id = i2.ingredient_id
            ORDER BY dnc.ingredient_a_id, dnc.ingredient_b_id
        """
        conflicts = self.db.execute_query(query)
        
        print("Current Conflicts (Global):")
        if conflicts:
            for c in conflicts:
                print(f"  {c['ing_a_name']} (ID: {c['ingredient_a_id']}) <-> "
                      f"{c['ing_b_name']} (ID: {c['ingredient_b_id']})")
        else:
            print("  (none)")
        print()
        
        action = input("Action: [a]dd, [r]emove, [c]ancel: ").strip().lower()
        if action == 'c':
            return
        
        # List ingredients
        ingredients = self.db.execute_query(
            "SELECT ingredient_id, name FROM Ingredient ORDER BY ingredient_id"
        )
        print("\nAvailable Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['name']}")
        
        ing_a_id = input("\nIngredient A ID: ").strip()
        if ing_a_id not in [str(i['ingredient_id']) for i in ingredients]:
            print("✗ Invalid ingredient ID")
            return
        
        ing_b_id = input("Ingredient B ID: ").strip()
        if ing_b_id not in [str(i['ingredient_id']) for i in ingredients]:
            print("✗ Invalid ingredient ID")
            return
        
        if ing_a_id == ing_b_id:
            print("✗ Cannot combine ingredient with itself")
            return
        
        # Ensure consistent ordering (smaller ID first) per schema CHECK constraint
        if ing_a_id > ing_b_id:
            ing_a_id, ing_b_id = ing_b_id, ing_a_id
        
        if action == 'a':
            query = """
                INSERT INTO DoNotCombine (ingredient_a_id, ingredient_b_id)
                VALUES (%s, %s)
            """
            if self.db.execute_update(query, (ing_a_id, ing_b_id)):
                print(f"✓ Conflict added")
        
        elif action == 'r':
            query = """
                DELETE FROM DoNotCombine
                WHERE ingredient_a_id = %s AND ingredient_b_id = %s
            """
            if self.db.execute_update(query, (ing_a_id, ing_b_id)):
                print(f"✓ Conflict removed")
    
    def maintain_formulations(self):
        """Maintain formulations and prices"""
        print("=" * 70)
        print("MAINTAIN FORMULATIONS")
        print("=" * 70)
        print()
        
        # List current formulations
        query = """
            SELECT f.formulation_id, i.name AS ingredient_name,
                   f.pack_size, f.unit_price, f.valid_from_date, f.valid_to_date
            FROM Formulation f
            JOIN Ingredient i ON f.ingredient_id = i.ingredient_id
            WHERE f.supplier_id = %s
            ORDER BY f.formulation_id, f.valid_from_date DESC
        """
        formulations = self.db.execute_query(query, (self.supplier_id,))
        
        print("Current Formulations:")
        if formulations:
            for f in formulations:
                valid_status = "Active" if f['valid_to_date'] is None else f"Until {f['valid_to_date']}"
                print(f"  [{f['formulation_id']}] {f['ingredient_name']}: "
                      f"Pack {f['pack_size']} @ ${f['unit_price']:.2f} "
                      f"(Valid: {f['valid_from_date']} to {valid_status})")
        else:
            print("  (none)")
        print()
        
        action = input("Action: [a]dd formulation, [e]dit formulation, [m]anage materials, [c]ancel: ").strip().lower()
        if action == 'c':
            return
        
        if action == 'a':
            # List all ingredients
            all_ingredients = self.db.execute_query(
                "SELECT ingredient_id, name FROM Ingredient ORDER BY ingredient_id"
            )
            
            if not all_ingredients:
                print("✗ No ingredients available.")
                return
            
            print("\nAvailable Ingredients:")
            for ing in all_ingredients:
                print(f"  [{ing['ingredient_id']}] {ing['name']}")
            
            ingredient_id = input("\nIngredient ID: ").strip()
            if ingredient_id not in [str(i['ingredient_id']) for i in all_ingredients]:
                print("✗ Invalid ingredient ID")
                return
            
            pack_size = input("Pack Size: ").strip()
            try:
                pack_size = float(pack_size)
                if pack_size <= 0:
                    print("✗ Pack size must be positive")
                    return
            except ValueError:
                print("✗ Invalid pack size")
                return
            
            unit_price = input("Unit Price per Pack: ").strip()
            try:
                unit_price = float(unit_price)
                if unit_price < 0:
                    print("✗ Price cannot be negative")
                    return
            except ValueError:
                print("✗ Invalid price")
                return
            
            valid_from_str = input("Valid From (YYYY-MM-DD) [today]: ").strip()
            if not valid_from_str:
                valid_from = datetime.now().date()
            else:
                try:
                    valid_from = datetime.strptime(valid_from_str, '%Y-%m-%d').date()
                except ValueError:
                    print("✗ Invalid date format")
                    return
            
            valid_to_str = input("Valid To (YYYY-MM-DD, optional): ").strip()
            valid_to = None
            if valid_to_str:
                try:
                    valid_to = datetime.strptime(valid_to_str, '%Y-%m-%d').date()
                except ValueError:
                    print("✗ Invalid date format")
                    return
            
            # Get next formulation ID
            next_form_id = self.db.get_next_id('Formulation', 'formulation_id')
            
            query = """
                INSERT INTO Formulation (formulation_id, supplier_id, ingredient_id, 
                                       pack_size, unit_price, valid_from_date, valid_to_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            if not self.db.execute_update(query, (next_form_id, self.supplier_id, ingredient_id, 
                                                   pack_size, unit_price, valid_from, valid_to)):
                return
            
            print(f"✓ Formulation {next_form_id} created")
            
            # Add materials if compound ingredient
            ingredient_type = self.db.execute_query(
                "SELECT ingredient_type FROM Ingredient WHERE ingredient_id = %s",
                (ingredient_id,)
            )
            if ingredient_type and ingredient_type[0]['ingredient_type'] == 'COMPOUND':
                self.manage_formulation_materials(next_form_id)
        
        elif action == 'm':
            form_id = input("Formulation ID: ").strip()
            if not form_id.isdigit():
                print("✗ Invalid formulation ID")
                return
            form_id = int(form_id)
            
            # Verify ownership
            owned = self.db.execute_query(
                "SELECT formulation_id FROM Formulation WHERE formulation_id = %s AND supplier_id = %s",
                (form_id, self.supplier_id)
            )
            if not owned:
                print("✗ Formulation not found or not owned by you")
                return
            
            self.manage_formulation_materials(form_id)
    
    def manage_formulation_materials(self, formulation_id: int):
        """Manage materials for a formulation (for compound ingredients)"""
        print(f"\nManaging materials for formulation {formulation_id}")
        
        # Show current materials
        query = """
            SELECT fm.material_ingredient_id, i.name AS ingredient_name, fm.quantity
            FROM FormulationMaterials fm
            JOIN Ingredient i ON fm.material_ingredient_id = i.ingredient_id
            WHERE fm.formulation_id = %s
        """
        materials = self.db.execute_query(query, (formulation_id,))
        
        if materials:
            print("Current Materials:")
            for m in materials:
                print(f"  {m['ingredient_name']} (ID: {m['material_ingredient_id']}): {m['quantity']} oz")
        else:
            print("No materials defined yet")
        
        print("\nAdd materials (press Enter with empty ingredient ID to finish):")
        
        while True:
            material_id = input("Material Ingredient ID: ").strip()
            if not material_id:
                break
            
            if material_id not in [str(i['ingredient_id']) for i in self.db.execute_query("SELECT ingredient_id FROM Ingredient")]:
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
            
            # Insert or update material
            mat_query = """
                INSERT INTO FormulationMaterials (formulation_id, material_ingredient_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = %s
            """
            if self.db.execute_update(mat_query, (formulation_id, material_id, qty, qty)):
                print(f"✓ Added {qty} oz of ingredient {material_id}")
    
    def create_ingredient_batch(self):
        """Create ingredient batch (lot intake)"""
        print("=" * 70)
        print("CREATE INGREDIENT BATCH (LOT INTAKE)")
        print("=" * 70)
        print()
        
        # List all ingredients
        all_ingredients = self.db.execute_query(
            "SELECT ingredient_id, name FROM Ingredient ORDER BY ingredient_id"
        )
        
        if not all_ingredients:
            print("✗ No ingredients available")
            return
        
        print("Available Ingredients:")
        for ing in all_ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['name']}")
        
        ingredient_id = input("\nIngredient ID: ").strip()
        if ingredient_id not in [str(i['ingredient_id']) for i in all_ingredients]:
            print("✗ Invalid ingredient ID")
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
        
        # Get supplier batch ID (trigger will generate lot_number)
        supplier_batch_id = input("Supplier Batch ID (for lot number): ").strip()
        if not supplier_batch_id:
            print("✗ Supplier Batch ID is required")
            return
        
        # Check if combination already exists (trigger will create lot_number)
        existing = self.db.execute_query(
            "SELECT lot_number FROM IngredientBatch WHERE ingredient_id = %s AND supplier_id = %s AND supplier_batch_id = %s",
            (ingredient_id, self.supplier_id, supplier_batch_id)
        )
        if existing:
            print(f"✗ Batch with ingredient_id={ingredient_id}, supplier_id={self.supplier_id}, supplier_batch_id={supplier_batch_id} already exists")
            return
        
        # Insert batch (trigger will generate lot_number)
        query = """
            INSERT INTO IngredientBatch 
            (ingredient_id, supplier_id, supplier_batch_id, quantity_on_hand, 
             per_unit_cost, expiration_date, intake_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        if self.db.execute_update(query, (ingredient_id, self.supplier_id, supplier_batch_id, quantity, per_unit_cost, expiration_date, intake_date)):
            # Get the generated lot number
            lot_result = self.db.execute_query(
                "SELECT lot_number FROM IngredientBatch WHERE ingredient_id = %s AND supplier_id = %s AND supplier_batch_id = %s",
                (ingredient_id, self.supplier_id, supplier_batch_id)
            )
            lot_number = lot_result[0]['lot_number'] if lot_result else "N/A"
            print(f"✓ Ingredient batch {lot_number} created successfully")
            print(f"  Quantity: {quantity} oz")
            print(f"  Cost per unit: ${per_unit_cost:.2f}")



