#!/usr/bin/env python3
"""
Queries Menu - Implements the 5 required queries
"""

from typing import List, Dict, Any
from db_helper import DatabaseHelper

class QueriesMenu:
    """Queries menu for the 5 required queries"""
    
    def __init__(self, db: DatabaseHelper):
        self.db = db
    
    def print_menu(self):
        """Print queries menu"""
        print("=" * 70)
        print("QUERIES")
        print("=" * 70)
        print("  [1] List ingredients and lot numbers for last batch of Steak Dinner (100) by MFG001")
        print("  [2] Suppliers and total spending for manufacturer MFG002")
        print("  [3] Unit cost for product batch 100-MFG001-B0901")
        print("  [4] Conflicting ingredients for product batch 100-MFG001-B0901")
        print("  [5] Manufacturers NOT supplied by James Miller (21)")
        print("  [0] Back")
        print()
    
    def run(self):
        """Run queries menu loop"""
        while True:
            self.print_menu()
            choice = input("Enter choice: ").strip()
            print()
            
            if choice == '0':
                break
            elif choice == '1':
                self.query1()
            elif choice == '2':
                self.query2()
            elif choice == '3':
                self.query3()
            elif choice == '4':
                self.query4()
            elif choice == '5':
                self.query5()
            else:
                print("✗ Invalid choice. Please try again.")
            print()
    
    def query1(self):
        """Query 1: List ingredients and lot numbers for last batch of Steak Dinner (100) by MFG001"""
        print("=" * 70)
        print("QUERY 1: Ingredients and lot numbers for last Steak Dinner batch by MFG001")
        print("=" * 70)
        print()
        
        query = """
            SELECT 
                i.ingredient_id,
                i.ingredient_name,
                bc.ingredient_lot_number,
                bc.quantity_used
            FROM Product_Batches pb
            JOIN Products p ON pb.product_id = p.product_id
            JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
            JOIN Batch_Consumption bc ON pb.batch_number = bc.product_batch_number
            JOIN Ingredient_Batches ib ON bc.ingredient_lot_number = ib.lot_number
            JOIN Ingredients i ON ib.ingredient_id = i.ingredient_id
            WHERE p.product_id = 100
              AND m.manufacturer_id = 1
              AND m.user_id = 'MFG001'
            ORDER BY pb.production_date DESC, pb.batch_number DESC
            LIMIT 1
        """
        
        # First get the batch number
        batch_query = """
            SELECT pb.batch_number, pb.production_date
            FROM Product_Batches pb
            JOIN Products p ON pb.product_id = p.product_id
            JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
            WHERE p.product_id = 100
              AND m.manufacturer_id = 1
              AND m.user_id = 'MFG001'
            ORDER BY pb.production_date DESC, pb.batch_number DESC
            LIMIT 1
        """
        
        batch_result = self.db.execute_query(batch_query)
        if not batch_result:
            print("No batches found for product 100 (Steak Dinner) by manufacturer MFG001")
            return
        
        batch_number = batch_result[0]['batch_number']
        print(f"Last Batch: {batch_number} (Production Date: {batch_result[0]['production_date']})")
        print()
        
        # Get ingredients for this batch
        results = self.db.execute_query(query)
        
        if not results:
            print("No ingredients found for this batch")
            return
        
        print("Ingredients and Lot Numbers:")
        print("-" * 70)
        print(f"{'Ingredient ID':<15} {'Ingredient Name':<30} {'Lot Number':<25} {'Quantity Used':<15}")
        print("-" * 70)
        
        for r in results:
            print(f"{r['ingredient_id']:<15} {r['ingredient_name']:<30} "
                  f"{r['ingredient_lot_number']:<25} {r['quantity_used']:<15.2f}")
    
    def query2(self):
        """Query 2: For manufacturer MFG002, list suppliers and total spending"""
        print("=" * 70)
        print("QUERY 2: Suppliers and total spending for manufacturer MFG002")
        print("=" * 70)
        print()
        
        query = """
            SELECT 
                s.supplier_id,
                s.supplier_name,
                SUM(bc.quantity_used * ib.cost_per_unit) as total_spent
            FROM Manufacturers m
            JOIN Products p ON m.manufacturer_id = p.manufacturer_id
            JOIN Product_Batches pb ON p.product_id = pb.product_id
            JOIN Batch_Consumption bc ON pb.batch_number = bc.product_batch_number
            JOIN Ingredient_Batches ib ON bc.ingredient_lot_number = ib.lot_number
            JOIN Suppliers s ON ib.supplier_id = s.supplier_id
            WHERE m.user_id = 'MFG002'
            GROUP BY s.supplier_id, s.supplier_name
            ORDER BY total_spent DESC
        """
        
        results = self.db.execute_query(query)
        
        if not results:
            print("No suppliers found for manufacturer MFG002")
            return
        
        print("Suppliers and Total Spending:")
        print("-" * 70)
        print(f"{'Supplier ID':<15} {'Supplier Name':<30} {'Total Spent':<20}")
        print("-" * 70)
        
        total_all = 0
        for r in results:
            total = float(r['total_spent']) if r['total_spent'] else 0
            total_all += total
            print(f"{r['supplier_id']:<15} {r['supplier_name']:<30} ${total:<19.2f}")
        
        print("-" * 70)
        print(f"{'TOTAL':<45} ${total_all:<19.2f}")
    
    def query3(self):
        """Query 3: Unit cost for product batch 100-MFG001-B0901"""
        print("=" * 70)
        print("QUERY 3: Unit cost for product batch 100-MFG001-B0901")
        print("=" * 70)
        print()
        
        query = """
            SELECT 
                pb.batch_number,
                p.product_name,
                pb.quantity_produced,
                pb.total_cost,
                pb.cost_per_unit
            FROM Product_Batches pb
            JOIN Products p ON pb.product_id = p.product_id
            WHERE pb.batch_number = '100-MFG001-B0901'
        """
        
        results = self.db.execute_query(query)
        
        if not results:
            print("Batch 100-MFG001-B0901 not found")
            return
        
        batch = results[0]
        print(f"Batch Number: {batch['batch_number']}")
        print(f"Product: {batch['product_name']}")
        print(f"Quantity Produced: {batch['quantity_produced']} units")
        print(f"Total Cost: ${batch['total_cost']:.2f}")
        print(f"Unit Cost: ${batch['cost_per_unit']:.2f}")
    
    def query4(self):
        """Query 4: Conflicting ingredients for product batch 100-MFG001-B0901"""
        print("=" * 70)
        print("QUERY 4: Conflicting ingredients for product batch 100-MFG001-B0901")
        print("=" * 70)
        print()
        
        # First get all ingredients used in this batch (flattened one level)
        ingredients_query = """
            SELECT DISTINCT COALESCE(ic.child_ingredient_id, ri.ingredient_id) as ingredient_id
            FROM Product_Batches pb
            JOIN Recipe_Plans rp ON pb.plan_id = rp.plan_id
            JOIN Recipe_Ingredients ri ON rp.plan_id = ri.plan_id
            JOIN Ingredients i ON ri.ingredient_id = i.ingredient_id
            LEFT JOIN Ingredient_Compositions ic ON i.ingredient_id = ic.parent_ingredient_id
            WHERE pb.batch_number = '100-MFG001-B0901'
        """
        
        ingredient_ids = self.db.execute_query(ingredients_query)
        if not ingredient_ids:
            print("Batch not found or has no ingredients")
            return
        
        ing_ids = [r['ingredient_id'] for r in ingredient_ids]
        
        if not ing_ids:
            print("No ingredients found for this batch")
            return
        
        # Find conflicts
        placeholders = ','.join(['%s'] * len(ing_ids))
        conflict_query = f"""
            SELECT DISTINCT 
                dnc.ingredient1_id,
                dnc.ingredient2_id,
                i1.ingredient_name as ing1_name,
                i2.ingredient_name as ing2_name,
                dnc.reason
            FROM Do_Not_Combine dnc
            JOIN Ingredients i1 ON dnc.ingredient1_id = i1.ingredient_id
            JOIN Ingredients i2 ON dnc.ingredient2_id = i2.ingredient_id
            WHERE (dnc.ingredient1_id IN ({placeholders}) AND dnc.ingredient2_id IN ({placeholders}))
               OR (dnc.ingredient1_id IN ({placeholders}) AND dnc.ingredient2_id IN ({placeholders}))
        """
        
        params = tuple(ing_ids + ing_ids)
        conflicts = self.db.execute_query(conflict_query, params)
        
        # Get all ingredients that conflict with any ingredient in the batch
        conflicting_ingredient_ids = set()
        for conflict in conflicts:
            if conflict['ingredient1_id'] in ing_ids:
                conflicting_ingredient_ids.add(conflict['ingredient2_id'])
            if conflict['ingredient2_id'] in ing_ids:
                conflicting_ingredient_ids.add(conflict['ingredient1_id'])
        
        # Remove ingredients already in the batch
        conflicting_ingredient_ids = conflicting_ingredient_ids - set(ing_ids)
        
        if not conflicting_ingredient_ids:
            print("No conflicting ingredients found (all conflicts are within the batch itself)")
            if conflicts:
                print("\nConflicts within the batch:")
                print("-" * 70)
                for c in conflicts:
                    print(f"  ✗ {c['ing1_name']} (ID: {c['ingredient1_id']}) <-> "
                          f"{c['ing2_name']} (ID: {c['ingredient2_id']})")
                    print(f"    Reason: {c['reason']}")
            return
        
        # Get ingredient names
        conflict_list = list(conflicting_ingredient_ids)
        conflict_placeholders = ','.join(['%s'] * len(conflict_list))
        ingredient_names_query = f"""
            SELECT ingredient_id, ingredient_name
            FROM Ingredients
            WHERE ingredient_id IN ({conflict_placeholders})
            ORDER BY ingredient_id
        """
        
        conflicting_ingredients = self.db.execute_query(ingredient_names_query, tuple(conflict_list))
        
        print("Ingredients that CANNOT be included (conflict with current ingredients):")
        print("-" * 70)
        print(f"{'Ingredient ID':<15} {'Ingredient Name':<30}")
        print("-" * 70)
        
        for ing in conflicting_ingredients:
            print(f"{ing['ingredient_id']:<15} {ing['ingredient_name']:<30}")
        
        if conflicts:
            print("\nDetected Conflicts:")
            print("-" * 70)
            for c in conflicts:
                print(f"  {c['ing1_name']} (ID: {c['ingredient1_id']}) <-> "
                      f"{c['ing2_name']} (ID: {c['ingredient2_id']})")
                print(f"    Reason: {c['reason']}")
    
    def query5(self):
        """Query 5: Manufacturers NOT supplied by James Miller (21)"""
        print("=" * 70)
        print("QUERY 5: Manufacturers NOT supplied by James Miller (supplier 21)")
        print("=" * 70)
        print()
        
        query = """
            SELECT DISTINCT m.manufacturer_id, m.manufacturer_name, m.user_id
            FROM Manufacturers m
            WHERE m.manufacturer_id NOT IN (
                SELECT DISTINCT p.manufacturer_id
                FROM Products p
                JOIN Product_Batches pb ON p.product_id = pb.product_id
                JOIN Batch_Consumption bc ON pb.batch_number = bc.product_batch_number
                JOIN Ingredient_Batches ib ON bc.ingredient_lot_number = ib.lot_number
                WHERE ib.supplier_id = 21
            )
            ORDER BY m.manufacturer_id
        """
        
        results = self.db.execute_query(query)
        
        if not results:
            print("All manufacturers have been supplied by James Miller (21)")
            return
        
        print("Manufacturers NOT supplied by James Miller (21):")
        print("-" * 70)
        print(f"{'Manufacturer ID':<18} {'User ID':<15} {'Manufacturer Name':<30}")
        print("-" * 70)
        
        for r in results:
            print(f"{r['manufacturer_id']:<18} {r['user_id']:<15} {r['manufacturer_name']:<30}")


