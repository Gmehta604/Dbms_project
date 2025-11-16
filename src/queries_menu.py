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
        
        # First get the last batch for product 100 by MFG001
        batch_query = """
            SELECT pb.lot_number, pb.production_date
            FROM ProductBatch pb
            JOIN Product p ON pb.product_id = p.product_id
            WHERE p.product_id = '100'
              AND pb.manufacturer_id = 'MFG001'
            ORDER BY pb.production_date DESC
            LIMIT 1
        """
        
        batch_result = self.db.execute_query(batch_query)
        if not batch_result:
            print("No batches found for product 100 (Steak Dinner) by manufacturer MFG001")
            return
        
        batch_lot_number = batch_result[0]['lot_number']
        print(f"Last Batch: {batch_lot_number} (Production Date: {batch_result[0]['production_date']})")
        print()
        
        # Get ingredients and lot numbers for this batch
        query = """
            SELECT 
                i.ingredient_id,
                i.name AS ingredient_name,
                bc.ingredient_lot_number,
                bc.quantity_consumed
            FROM BatchConsumption bc
            JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
            JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
            WHERE bc.product_lot_number = %s
            ORDER BY i.ingredient_id
        """
        
        results = self.db.execute_query(query, (batch_lot_number,))
        
        if not results:
            print("No ingredients found for this batch")
            return
        
        print("Ingredients and Lot Numbers:")
        print("-" * 70)
        print(f"{'Ingredient ID':<15} {'Ingredient Name':<30} {'Lot Number':<25} {'Quantity Used':<15}")
        print("-" * 70)
        
        for r in results:
            print(f"{r['ingredient_id']:<15} {r['ingredient_name']:<30} "
                  f"{r['ingredient_lot_number']:<25} {r['quantity_consumed']:<15.2f}")
    
    def query2(self):
        """Query 2: For manufacturer MFG002, list suppliers and total spending"""
        print("=" * 70)
        print("QUERY 2: Suppliers and total spending for manufacturer MFG002")
        print("=" * 70)
        print()
        
        query = """
            SELECT 
                s.supplier_id,
                s.name AS supplier_name,
                SUM(bc.quantity_consumed * ib.per_unit_cost) AS total_spent
            FROM ProductBatch pb
            JOIN BatchConsumption bc ON pb.lot_number = bc.product_lot_number
            JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
            JOIN Supplier s ON ib.supplier_id = s.supplier_id
            WHERE pb.manufacturer_id = 'MFG002'
            GROUP BY s.supplier_id, s.name
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
                pb.lot_number,
                p.name AS product_name,
                pb.produced_quantity,
                pb.total_batch_cost,
                (pb.total_batch_cost / pb.produced_quantity) AS unit_cost
            FROM ProductBatch pb
            JOIN Product p ON pb.product_id = p.product_id
            WHERE pb.lot_number = '100-MFG001-B0901'
        """
        
        results = self.db.execute_query(query)
        
        if not results:
            print("Batch 100-MFG001-B0901 not found")
            return
        
        batch = results[0]
        print(f"Lot Number: {batch['lot_number']}")
        print(f"Product: {batch['product_name']}")
        print(f"Quantity Produced: {batch['produced_quantity']} units")
        print(f"Total Cost: ${batch['total_batch_cost']:.2f}")
        print(f"Unit Cost: ${batch['unit_cost']:.2f}")
    
    def query4(self):
        """Query 4: Conflicting ingredients for product batch 100-MFG001-B0901"""
        print("=" * 70)
        print("QUERY 4: Conflicting ingredients for product batch 100-MFG001-B0901")
        print("=" * 70)
        print()
        
        # First get all ingredients used in this batch (from actual consumption)
        ingredients_query = """
            SELECT DISTINCT i.ingredient_id
            FROM BatchConsumption bc
            JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
            JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
            WHERE bc.product_lot_number = '100-MFG001-B0901'
        """
        
        ingredient_ids = self.db.execute_query(ingredients_query)
        if not ingredient_ids:
            print("Batch not found or has no ingredients")
            return
        
        ing_ids = [r['ingredient_id'] for r in ingredient_ids if r['ingredient_id']]
        
        if not ing_ids:
            print("No ingredients found for this batch")
            return
        
        # Find conflicts - DoNotCombine uses ingredient_a_id and ingredient_b_id
        placeholders = ','.join(['%s'] * len(ing_ids))
        conflict_query = f"""
            SELECT DISTINCT 
                dnc.ingredient_a_id,
                dnc.ingredient_b_id,
                i1.name AS ing_a_name,
                i2.name AS ing_b_name
            FROM DoNotCombine dnc
            JOIN Ingredient i1 ON dnc.ingredient_a_id = i1.ingredient_id
            JOIN Ingredient i2 ON dnc.ingredient_b_id = i2.ingredient_id
            WHERE (dnc.ingredient_a_id IN ({placeholders}) AND dnc.ingredient_b_id IN ({placeholders}))
        """
        
        conflicts = self.db.execute_query(conflict_query, tuple(ing_ids + ing_ids))
        
        if not conflicts:
            print("No conflicting ingredients found in this batch")
            return
        
        print("Conflicting Ingredients in Batch:")
        print("-" * 70)
        print(f"{'Ingredient A':<35} {'Ingredient B':<35}")
        print("-" * 70)
        
        for c in conflicts:
            ing_a_str = f"{c['ing_a_name']} (ID: {c['ingredient_a_id']})"
            ing_b_str = f"{c['ing_b_name']} (ID: {c['ingredient_b_id']})"
            print(f"{ing_a_str:<35} {ing_b_str:<35}")
        
        # Also find ingredients that would conflict if added
        conflicting_outside = set()
        for conflict in conflicts:
            if conflict['ingredient_a_id'] in ing_ids:
                if conflict['ingredient_b_id'] not in ing_ids:
                    conflicting_outside.add(conflict['ingredient_b_id'])
            if conflict['ingredient_b_id'] in ing_ids:
                if conflict['ingredient_a_id'] not in ing_ids:
                    conflicting_outside.add(conflict['ingredient_a_id'])
        
        if conflicting_outside:
            conflict_list = list(conflicting_outside)
            conflict_placeholders = ','.join(['%s'] * len(conflict_list))
            ingredient_names_query = f"""
                SELECT ingredient_id, name AS ingredient_name
                FROM Ingredient
                WHERE ingredient_id IN ({conflict_placeholders})
                ORDER BY ingredient_id
            """
            
            conflicting_ingredients = self.db.execute_query(ingredient_names_query, tuple(conflict_list))
            
            print("\nIngredients that CANNOT be added (would conflict with current ingredients):")
            print("-" * 70)
            print(f"{'Ingredient ID':<15} {'Ingredient Name':<30}")
            print("-" * 70)
            
            for ing in conflicting_ingredients:
                print(f"{ing['ingredient_id']:<15} {ing['ingredient_name']:<30}")
    
    def query5(self):
        """Query 5: Manufacturers NOT supplied by James Miller (21)"""
        print("=" * 70)
        print("QUERY 5: Manufacturers NOT supplied by James Miller (supplier 21)")
        print("=" * 70)
        print()
        
        query = """
            SELECT DISTINCT m.manufacturer_id, m.name AS manufacturer_name
            FROM Manufacturer m
            WHERE m.manufacturer_id NOT IN (
                SELECT DISTINCT pb.manufacturer_id
                FROM ProductBatch pb
                JOIN BatchConsumption bc ON pb.lot_number = bc.product_lot_number
                JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
                WHERE ib.supplier_id = '21'
            )
            ORDER BY m.manufacturer_id
        """
        
        results = self.db.execute_query(query)
        
        if not results:
            print("All manufacturers have been supplied by James Miller (21)")
            return
        
        print("Manufacturers NOT supplied by James Miller (21):")
        print("-" * 70)
        print(f"{'Manufacturer ID':<18} {'Manufacturer Name':<50}")
        print("-" * 70)
        
        for r in results:
            print(f"{r['manufacturer_id']:<18} {r['manufacturer_name']:<50}")



