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
        
        # List currently supplied ingredients
        query = """
            SELECT i.ingredient_id, i.ingredient_name, si.is_active
            FROM Supplier_Ingredients si
            JOIN Ingredients i ON si.ingredient_id = i.ingredient_id
            WHERE si.supplier_id = %s
            ORDER BY i.ingredient_id
        """
        supplied = self.db.execute_query(query, (self.supplier_id,))
        
        print("Currently Supplied Ingredients:")
        if supplied:
            for ing in supplied:
                status = "Active" if ing['is_active'] else "Inactive"
                print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']} - {status}")
        else:
            print("  (none)")
        print()
        
        # List all ingredients
        all_ingredients = self.db.execute_query(
            "SELECT ingredient_id, ingredient_name FROM Ingredients ORDER BY ingredient_id"
        )
        
        print("All Available Ingredients:")
        for ing in all_ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']}")
        print()
        
        action = input("Action: [a]dd, [r]emove, [t]oggle active, [c]ancel: ").strip().lower()
        if action == 'c':
            return
        
        ingredient_id = input("Ingredient ID: ").strip()
        if not ingredient_id.isdigit() or int(ingredient_id) not in [i['ingredient_id'] for i in all_ingredients]:
            print("✗ Invalid ingredient ID")
            return
        ingredient_id = int(ingredient_id)
        
        if action == 'a':
            # Add ingredient
            query = """
                INSERT INTO Supplier_Ingredients (supplier_id, ingredient_id, is_active)
                VALUES (%s, %s, TRUE)
                ON DUPLICATE KEY UPDATE is_active = TRUE
            """
            if self.db.execute_update(query, (self.supplier_id, ingredient_id)):
                print(f"✓ Ingredient {ingredient_id} added to supplied list")
        
        elif action == 'r':
            # Remove ingredient (set inactive)
            query = """
                UPDATE Supplier_Ingredients 
                SET is_active = FALSE
                WHERE supplier_id = %s AND ingredient_id = %s
            """
            if self.db.execute_update(query, (self.supplier_id, ingredient_id)):
                print(f"✓ Ingredient {ingredient_id} removed from supplied list")
        
        elif action == 't':
            # Toggle active status
            current = self.db.execute_query(
                "SELECT is_active FROM Supplier_Ingredients WHERE supplier_id = %s AND ingredient_id = %s",
                (self.supplier_id, ingredient_id)
            )
            if current:
                new_status = not current[0]['is_active']
                query = """
                    UPDATE Supplier_Ingredients 
                    SET is_active = %s
                    WHERE supplier_id = %s AND ingredient_id = %s
                """
                if self.db.execute_update(query, (new_status, self.supplier_id, ingredient_id)):
                    status_str = "activated" if new_status else "deactivated"
                    print(f"✓ Ingredient {ingredient_id} {status_str}")
            else:
                print("✗ Ingredient not in supplied list")
    
    def define_update_ingredient(self):
        """Define or update an ingredient (atomic or compound)"""
        print("=" * 70)
        print("DEFINE/UPDATE INGREDIENT")
        print("=" * 70)
        print()
        
        # List existing ingredients
        ingredients = self.db.execute_query(
            "SELECT ingredient_id, ingredient_name, ingredient_type FROM Ingredients ORDER BY ingredient_id"
        )
        
        print("Existing Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']} ({ing['ingredient_type']})")
        print()
        
        action = input("Create new ingredient? (y/n): ").strip().lower()
        if action != 'y':
            # Update existing
            ing_id = input("Ingredient ID to update: ").strip()
            if not ing_id.isdigit():
                print("✗ Invalid ingredient ID")
                return
            ing_id = int(ing_id)
            
            existing = self.db.execute_query(
                "SELECT * FROM Ingredients WHERE ingredient_id = %s",
                (ing_id,)
            )
            if not existing:
                print("✗ Ingredient not found")
                return
            
            ing = existing[0]
            print(f"\nCurrent: {ing['ingredient_name']} ({ing['ingredient_type']})")
            
            name = input(f"Name [{ing['ingredient_name']}]: ").strip() or ing['ingredient_name']
            ing_type = input(f"Type (Atomic/Compound) [{ing['ingredient_type']}]: ").strip().capitalize() or ing['ingredient_type']
            if ing_type not in ['Atomic', 'Compound']:
                print("✗ Type must be Atomic or Compound")
                return
            
            unit = input(f"Unit of Measure [{ing['unit_of_measure'] or ''}]: ").strip() or None
            desc = input(f"Description [{ing['description'] or ''}]: ").strip() or None
            
            query = """
                UPDATE Ingredients 
                SET ingredient_name = %s, ingredient_type = %s, 
                    unit_of_measure = %s, description = %s
                WHERE ingredient_id = %s
            """
            if self.db.execute_update(query, (name, ing_type, unit, desc, ing_id)):
                print(f"✓ Ingredient {ing_id} updated")
            
            # If compound, manage composition
            if ing_type == 'Compound':
                self.manage_ingredient_composition(ing_id)
            
            return
        
        # Create new ingredient
        ingredient_id = input("Ingredient ID: ").strip()
        if not ingredient_id.isdigit():
            print("✗ Ingredient ID must be an integer")
            return
        ingredient_id = int(ingredient_id)
        
        # Check if exists
        existing = self.db.execute_query(
            "SELECT ingredient_id FROM Ingredients WHERE ingredient_id = %s",
            (ingredient_id,)
        )
        if existing:
            print("✗ Ingredient ID already exists")
            return
        
        ingredient_name = input("Ingredient Name: ").strip()
        if not ingredient_name:
            print("✗ Ingredient name is required")
            return
        
        ingredient_type = input("Type (Atomic/Compound): ").strip().capitalize()
        if ingredient_type not in ['Atomic', 'Compound']:
            print("✗ Type must be Atomic or Compound")
            return
        
        unit_of_measure = input("Unit of Measure (default: oz): ").strip() or 'oz'
        description = input("Description (optional): ").strip() or None
        
        # Insert ingredient
        query = """
            INSERT INTO Ingredients (ingredient_id, ingredient_name, ingredient_type, 
                                   unit_of_measure, description)
            VALUES (%s, %s, %s, %s, %s)
        """
        if not self.db.execute_update(query, (ingredient_id, ingredient_name, ingredient_type, unit_of_measure, description)):
            return
        
        print(f"✓ Ingredient {ingredient_id} created")
        
        # If compound, add composition
        if ingredient_type == 'Compound':
            self.manage_ingredient_composition(ingredient_id)
    
    def manage_ingredient_composition(self, parent_ingredient_id: int):
        """Manage composition of a compound ingredient"""
        print(f"\nManaging composition for ingredient {parent_ingredient_id}")
        
        # Show current composition
        query = """
            SELECT ic.child_ingredient_id, i.ingredient_name, ic.quantity_required
            FROM Ingredient_Compositions ic
            JOIN Ingredients i ON ic.child_ingredient_id = i.ingredient_id
            WHERE ic.parent_ingredient_id = %s
        """
        composition = self.db.execute_query(query, (parent_ingredient_id,))
        
        if composition:
            print("Current Composition:")
            for comp in composition:
                print(f"  {comp['ingredient_name']} (ID: {comp['child_ingredient_id']}): {comp['quantity_required']} oz")
        else:
            print("No composition defined yet")
        
        print("\nAdd materials (one-level children only):")
        print("(Press Enter with empty ingredient ID to finish)")
        
        while True:
            child_id = input("Child Ingredient ID: ").strip()
            if not child_id:
                break
            
            if not child_id.isdigit():
                print("✗ Invalid ingredient ID")
                continue
            
            child_id = int(child_id)
            if child_id == parent_ingredient_id:
                print("✗ Cannot add self as child")
                continue
            
            # Check if ingredient exists
            exists = self.db.execute_query(
                "SELECT ingredient_id FROM Ingredients WHERE ingredient_id = %s",
                (child_id,)
            )
            if not exists:
                print("✗ Ingredient not found")
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
            
            # Insert or update composition
            comp_query = """
                INSERT INTO Ingredient_Compositions (parent_ingredient_id, child_ingredient_id, quantity_required)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity_required = %s
            """
            if self.db.execute_update(comp_query, (parent_ingredient_id, child_id, qty, qty)):
                print(f"✓ Added {qty} oz of ingredient {child_id}")
    
    def maintain_do_not_combine(self):
        """Maintain do-not-combine list (Grad feature)"""
        print("=" * 70)
        print("MAINTAIN DO-NOT-COMBINE LIST")
        print("=" * 70)
        print()
        
        # List current conflicts
        query = """
            SELECT dnc.ingredient1_id, dnc.ingredient2_id,
                   i1.ingredient_name as ing1_name, i2.ingredient_name as ing2_name,
                   dnc.reason
            FROM Do_Not_Combine dnc
            JOIN Ingredients i1 ON dnc.ingredient1_id = i1.ingredient_id
            JOIN Ingredients i2 ON dnc.ingredient2_id = i2.ingredient_id
            WHERE dnc.supplier_id = %s
            ORDER BY dnc.ingredient1_id, dnc.ingredient2_id
        """
        conflicts = self.db.execute_query(query, (self.supplier_id,))
        
        print("Current Conflicts:")
        if conflicts:
            for c in conflicts:
                print(f"  {c['ing1_name']} (ID: {c['ingredient1_id']}) <-> "
                      f"{c['ing2_name']} (ID: {c['ingredient2_id']}) - {c['reason']}")
        else:
            print("  (none)")
        print()
        
        action = input("Action: [a]dd, [r]emove, [c]ancel: ").strip().lower()
        if action == 'c':
            return
        
        # List ingredients
        ingredients = self.db.execute_query(
            "SELECT ingredient_id, ingredient_name FROM Ingredients ORDER BY ingredient_id"
        )
        print("\nAvailable Ingredients:")
        for ing in ingredients:
            print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']}")
        
        ing1_id = input("\nIngredient 1 ID: ").strip()
        if not ing1_id.isdigit() or int(ing1_id) not in [i['ingredient_id'] for i in ingredients]:
            print("✗ Invalid ingredient ID")
            return
        ing1_id = int(ing1_id)
        
        ing2_id = input("Ingredient 2 ID: ").strip()
        if not ing2_id.isdigit() or int(ing2_id) not in [i['ingredient_id'] for i in ingredients]:
            print("✗ Invalid ingredient ID")
            return
        ing2_id = int(ing2_id)
        
        if ing1_id == ing2_id:
            print("✗ Cannot combine ingredient with itself")
            return
        
        # Ensure consistent ordering (smaller ID first)
        if ing1_id > ing2_id:
            ing1_id, ing2_id = ing2_id, ing1_id
        
        if action == 'a':
            reason = input("Reason: ").strip() or "Regulatory restriction"
            
            query = """
                INSERT INTO Do_Not_Combine (supplier_id, ingredient1_id, ingredient2_id, reason, created_date)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE reason = %s
            """
            if self.db.execute_update(query, (self.supplier_id, ing1_id, ing2_id, reason, datetime.now().date(), reason)):
                print(f"✓ Conflict added")
        
        elif action == 'r':
            query = """
                DELETE FROM Do_Not_Combine
                WHERE supplier_id = %s AND ingredient1_id = %s AND ingredient2_id = %s
            """
            if self.db.execute_update(query, (self.supplier_id, ing1_id, ing2_id)):
                print(f"✓ Conflict removed")
    
    def maintain_formulations(self):
        """Maintain formulations and prices"""
        print("=" * 70)
        print("MAINTAIN FORMULATIONS")
        print("=" * 70)
        print()
        
        # List current formulations
        query = """
            SELECT f.formulation_id, f.name, i.ingredient_name,
                   fv.version_no, fv.pack_size, fv.unit_price, fv.is_active
            FROM Formulations f
            JOIN Ingredients i ON f.ingredient_id = i.ingredient_id
            LEFT JOIN Formulation_Versions fv ON f.formulation_id = fv.formulation_id
            WHERE f.supplier_id = %s
            ORDER BY f.formulation_id, fv.version_no DESC
        """
        formulations = self.db.execute_query(query, (self.supplier_id,))
        
        print("Current Formulations:")
        current_form_id = None
        for f in formulations:
            if f['formulation_id'] != current_form_id:
                print(f"\n  [{f['formulation_id']}] {f['name']} - {f['ingredient_name']}")
                current_form_id = f['formulation_id']
            if f['version_no']:
                status = "Active" if f['is_active'] else "Inactive"
                print(f"      Version {f['version_no']}: Pack {f['pack_size']} @ ${f['unit_price']:.2f} - {status}")
        print()
        
        action = input("Action: [a]dd formulation, [u]pdate version, [c]ancel: ").strip().lower()
        if action == 'c':
            return
        
        if action == 'a':
            # List supplied ingredients
            supplied = self.db.execute_query(
                """
                SELECT i.ingredient_id, i.ingredient_name
                FROM Supplier_Ingredients si
                JOIN Ingredients i ON si.ingredient_id = i.ingredient_id
                WHERE si.supplier_id = %s AND si.is_active = TRUE
                ORDER BY i.ingredient_id
                """
            , (self.supplier_id,))
            
            if not supplied:
                print("✗ No active supplied ingredients. Add ingredients first.")
                return
            
            print("\nSupplied Ingredients:")
            for ing in supplied:
                print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']}")
            
            ingredient_id = input("\nIngredient ID: ").strip()
            if not ingredient_id.isdigit() or int(ingredient_id) not in [i['ingredient_id'] for i in supplied]:
                print("✗ Invalid ingredient ID")
                return
            ingredient_id = int(ingredient_id)
            
            formulation_name = input("Formulation Name: ").strip()
            if not formulation_name:
                print("✗ Formulation name is required")
                return
            
            # Get next formulation ID
            next_form_id = self.db.get_next_id('Formulations', 'formulation_id')
            
            query = """
                INSERT INTO Formulations (formulation_id, supplier_id, ingredient_id, name)
                VALUES (%s, %s, %s, %s)
            """
            if not self.db.execute_update(query, (next_form_id, self.supplier_id, ingredient_id, formulation_name)):
                return
            
            print(f"✓ Formulation {next_form_id} created")
            
            # Add version
            self.add_formulation_version(next_form_id)
        
        elif action == 'u':
            form_id = input("Formulation ID: ").strip()
            if not form_id.isdigit():
                print("✗ Invalid formulation ID")
                return
            form_id = int(form_id)
            
            # Verify ownership
            owned = self.db.execute_query(
                "SELECT formulation_id FROM Formulations WHERE formulation_id = %s AND supplier_id = %s",
                (form_id, self.supplier_id)
            )
            if not owned:
                print("✗ Formulation not found or not owned by you")
                return
            
            self.add_formulation_version(form_id)
    
    def add_formulation_version(self, formulation_id: int):
        """Add a new version to a formulation"""
        # Get next version number
        version_query = """
            SELECT COALESCE(MAX(version_no), 0) + 1 AS next_version
            FROM Formulation_Versions
            WHERE formulation_id = %s
        """
        version_result = self.db.execute_query(version_query, (formulation_id,))
        next_version = version_result[0]['next_version'] if version_result else 1
        
        # Get next version ID
        next_version_id = self.db.get_next_id('Formulation_Versions', 'version_id')
        
        pack_size = input(f"Pack Size (version {next_version}): ").strip()
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
        
        effective_from = input("Effective From (YYYY-MM-DD) [today]: ").strip()
        if not effective_from:
            effective_from = datetime.now().date()
        else:
            try:
                effective_from = datetime.strptime(effective_from, '%Y-%m-%d').date()
            except ValueError:
                print("✗ Invalid date format")
                return
        
        effective_to = input("Effective To (YYYY-MM-DD, optional): ").strip()
        if effective_to:
            try:
                effective_to = datetime.strptime(effective_to, '%Y-%m-%d').date()
            except ValueError:
                print("✗ Invalid date format")
                return
        else:
            effective_to = None
        
        query = """
            INSERT INTO Formulation_Versions 
            (version_id, formulation_id, version_no, pack_size, unit_price, 
             effective_from, effective_to, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        """
        if self.db.execute_update(query, (next_version_id, formulation_id, next_version, pack_size, unit_price, effective_from, effective_to, True)):
            print(f"✓ Version {next_version} added")
    
    def create_ingredient_batch(self):
        """Create ingredient batch (lot intake)"""
        print("=" * 70)
        print("CREATE INGREDIENT BATCH (LOT INTAKE)")
        print("=" * 70)
        print()
        
        # List supplied ingredients
        supplied = self.db.execute_query(
            """
            SELECT i.ingredient_id, i.ingredient_name
            FROM Supplier_Ingredients si
            JOIN Ingredients i ON si.ingredient_id = i.ingredient_id
            WHERE si.supplier_id = %s AND si.is_active = TRUE
            ORDER BY i.ingredient_id
            """
        , (self.supplier_id,))
        
        if not supplied:
            print("✗ No active supplied ingredients. Add ingredients first.")
            return
        
        print("Supplied Ingredients:")
        for ing in supplied:
            print(f"  [{ing['ingredient_id']}] {ing['ingredient_name']}")
        
        ingredient_id = input("\nIngredient ID: ").strip()
        if not ingredient_id.isdigit() or int(ingredient_id) not in [i['ingredient_id'] for i in supplied]:
            print("✗ Invalid ingredient ID or not supplied by you")
            return
        ingredient_id = int(ingredient_id)
        
        # Check if ingredient has formulations
        formulations = self.db.execute_query(
            """
            SELECT f.formulation_id, fv.version_id, fv.version_no, fv.is_active
            FROM Formulations f
            LEFT JOIN Formulation_Versions fv ON f.formulation_id = fv.formulation_id
            WHERE f.supplier_id = %s AND f.ingredient_id = %s
            ORDER BY f.formulation_id, fv.version_no DESC
            """
        , (self.supplier_id, ingredient_id))
        
        version_id = None
        if formulations and formulations[0]['version_id']:
            print("\nAvailable Formulation Versions:")
            for f in formulations:
                if f['version_id']:
                    status = "Active" if f['is_active'] else "Inactive"
                    print(f"  [{f['version_id']}] Formulation {f['formulation_id']}, Version {f['version_no']} - {status}")
            
            version_input = input("\nVersion ID (optional, press Enter for none): ").strip()
            if version_input.isdigit():
                version_id = int(version_input)
        
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
        
        lot_number = f"{ingredient_id}-{self.supplier_id}-{batch_id}"
        
        # Check if lot number exists
        existing = self.db.execute_query(
            "SELECT lot_number FROM Ingredient_Batches WHERE lot_number = %s",
            (lot_number,)
        )
        if existing:
            print(f"✗ Lot number {lot_number} already exists")
            return
        
        # Insert batch (trigger will handle lot number format validation)
        query = """
            INSERT INTO Ingredient_Batches 
            (lot_number, ingredient_id, supplier_id, version_id, quantity_on_hand, 
             cost_per_unit, expiration_date, received_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        if self.db.execute_update(query, (lot_number, ingredient_id, self.supplier_id, version_id, quantity, cost_per_unit, expiration_date, received_date)):
            print(f"✓ Ingredient batch {lot_number} created successfully")
            print(f"  Quantity: {quantity} oz")
            print(f"  Cost per unit: ${cost_per_unit:.2f}")


