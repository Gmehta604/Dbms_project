#!/usr/bin/env python3
"""
Viewer Menu and Functions
"""

from typing import Optional, List, Dict, Any
from db_helper import DatabaseHelper

class ViewerMenu:
    """Viewer role menu and operations"""
    
    def __init__(self, db: DatabaseHelper, user: Dict[str, Any]):
        self.db = db
        self.user = user
    
    def print_menu(self):
        """Print viewer menu"""
        print("=" * 70)
        print("VIEWER MENU")
        print("=" * 70)
        print("  [1] Browse Product Types")
        print("  [2] Generate Ingredient List")
        print("  [3] Compare Two Product Types (Grad)")
        print("  [0] Logout")
        print()
    
    def run(self):
        """Run viewer menu loop"""
        while True:
            self.print_menu()
            choice = input("Enter choice: ").strip()
            print()
            
            if choice == '0':
                break
            elif choice == '1':
                self.browse_products()
            elif choice == '2':
                self.generate_ingredient_list()
            elif choice == '3':
                self.compare_products()
            else:
                print("✗ Invalid choice. Please try again.")
            print()
    
    def browse_products(self):
        """Browse product types organized by manufacturer and category"""
        print("=" * 70)
        print("BROWSE PRODUCT TYPES")
        print("=" * 70)
        print()
        
        query = """
            SELECT p.product_id, p.product_number, p.product_name,
                   m.manufacturer_name, c.category_name, p.standard_batch_size, p.created_date
            FROM Products p
            JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
            JOIN Categories c ON p.category_id = c.category_id
            ORDER BY m.manufacturer_name, c.category_name, p.product_name
        """
        products = self.db.execute_query(query)
        
        if not products:
            print("No products found")
            return
        
        current_manufacturer = None
        current_category = None
        
        for p in products:
            if p['manufacturer_name'] != current_manufacturer:
                current_manufacturer = p['manufacturer_name']
                print(f"\n{'='*70}")
                print(f"Manufacturer: {current_manufacturer}")
                print(f"{'='*70}")
                current_category = None
            
            if p['category_name'] != current_category:
                current_category = p['category_name']
                print(f"\n  Category: {current_category}")
                print(f"  {'-'*66}")
            
            print(f"    [{p['product_id']}] {p['product_name']}")
            if p['product_number']:
                print(f"        Product Number: {p['product_number']}")
            print(f"        Batch Size: {p['standard_batch_size']} units")
            print(f"        Created: {p['created_date']}")
            print()
    
    def generate_ingredient_list(self):
        """Generate flattened ingredient list for a product"""
        print("=" * 70)
        print("GENERATE INGREDIENT LIST")
        print("=" * 70)
        print()
        
        # List products
        products = self.db.execute_query(
            """
            SELECT p.product_id, p.product_name, m.manufacturer_name
            FROM Products p
            JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
            ORDER BY p.product_id
            """
        )
        
        if not products:
            print("No products found")
            return
        
        print("Available Products:")
        for p in products:
            print(f"  [{p['product_id']}] {p['product_name']} - {p['manufacturer_name']}")
        
        product_id = input("\nProduct ID: ").strip()
        if not product_id.isdigit() or int(product_id) not in [p['product_id'] for p in products]:
            print("✗ Invalid product ID")
            return
        product_id = int(product_id)
        
        # Get active recipe plan
        plan_query = """
            SELECT plan_id, version_number
            FROM Recipe_Plans
            WHERE product_id = %s AND is_active = TRUE
            ORDER BY version_number DESC
            LIMIT 1
        """
        plans = self.db.execute_query(plan_query, (product_id,))
        
        if not plans:
            print("✗ No active recipe plan found for this product")
            return
        
        plan_id = plans[0]['plan_id']
        
        # Get recipe ingredients and flatten one level (expand compounds)
        query = """
            SELECT 
                COALESCE(ic.child_ingredient_id, ri.ingredient_id) as ingredient_id,
                COALESCE(ci.ingredient_name, i.ingredient_name) as ingredient_name,
                SUM(ri.quantity_required * COALESCE(ic.quantity_required, 1)) as total_quantity
            FROM Recipe_Ingredients ri
            JOIN Ingredients i ON ri.ingredient_id = i.ingredient_id
            LEFT JOIN Ingredient_Compositions ic ON i.ingredient_id = ic.parent_ingredient_id
            LEFT JOIN Ingredients ci ON ic.child_ingredient_id = ci.ingredient_id
            WHERE ri.plan_id = %s
            GROUP BY ingredient_id, ingredient_name
            ORDER BY total_quantity DESC
        """
        ingredients = self.db.execute_query(query, (plan_id,))
        
        if not ingredients:
            print("No ingredients found")
            return
        
        product = next(p for p in products if p['product_id'] == product_id)
        print(f"\nIngredient List for: {product['product_name']} (Product ID: {product_id})")
        print("=" * 70)
        print(f"{'Ingredient ID':<15} {'Ingredient Name':<30} {'Quantity (oz)':<15}")
        print("-" * 70)
        
        for ing in ingredients:
            print(f"{ing['ingredient_id']:<15} {ing['ingredient_name']:<30} {ing['total_quantity']:<15.2f}")
    
    def compare_products(self):
        """Compare two product types for incompatibilities (Grad feature)"""
        print("=" * 70)
        print("COMPARE PRODUCT TYPES FOR INCOMPATIBILITIES")
        print("=" * 70)
        print()
        
        # List products
        products = self.db.execute_query(
            """
            SELECT p.product_id, p.product_name, m.manufacturer_name
            FROM Products p
            JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
            ORDER BY p.product_id
            """
        )
        
        if not products:
            print("No products found")
            return
        
        print("Available Products:")
        for p in products:
            print(f"  [{p['product_id']}] {p['product_name']} - {p['manufacturer_name']}")
        
        product1_id = input("\nProduct 1 ID: ").strip()
        if not product1_id.isdigit() or int(product1_id) not in [p['product_id'] for p in products]:
            print("✗ Invalid product ID")
            return
        product1_id = int(product1_id)
        
        product2_id = input("Product 2 ID: ").strip()
        if not product2_id.isdigit() or int(product2_id) not in [p['product_id'] for p in products]:
            print("✗ Invalid product ID")
            return
        product2_id = int(product2_id)
        
        if product1_id == product2_id:
            print("✗ Cannot compare product with itself")
            return
        
        # Get flattened ingredient sets for both products
        def get_flattened_ingredients(prod_id):
            plan_query = """
                SELECT plan_id FROM Recipe_Plans
                WHERE product_id = %s AND is_active = TRUE
                ORDER BY version_number DESC LIMIT 1
            """
            plans = self.db.execute_query(plan_query, (prod_id,))
            if not plans:
                return set()
            
            plan_id = plans[0]['plan_id']
            query = """
                SELECT DISTINCT COALESCE(ic.child_ingredient_id, ri.ingredient_id) as ingredient_id
                FROM Recipe_Ingredients ri
                JOIN Ingredients i ON ri.ingredient_id = i.ingredient_id
                LEFT JOIN Ingredient_Compositions ic ON i.ingredient_id = ic.parent_ingredient_id
                WHERE ri.plan_id = %s
            """
            results = self.db.execute_query(query, (plan_id,))
            return set(r['ingredient_id'] for r in results)
        
        ing_set1 = get_flattened_ingredients(product1_id)
        ing_set2 = get_flattened_ingredients(product2_id)
        
        if not ing_set1 or not ing_set2:
            print("✗ One or both products have no active recipe plans")
            return
        
        # Check for conflicts in the union
        union_ingredients = list(ing_set1 | ing_set2)
        
        if not union_ingredients:
            print("No ingredients to compare")
            return
        
        # Check for do-not-combine pairs
        placeholders = ','.join(['%s'] * len(union_ingredients))
        conflict_query = f"""
            SELECT DISTINCT dnc.ingredient1_id, dnc.ingredient2_id,
                   i1.ingredient_name as ing1_name, i2.ingredient_name as ing2_name,
                   dnc.reason
            FROM Do_Not_Combine dnc
            JOIN Ingredients i1 ON dnc.ingredient1_id = i1.ingredient_id
            JOIN Ingredients i2 ON dnc.ingredient2_id = i2.ingredient_id
            WHERE (dnc.ingredient1_id IN ({placeholders}) AND dnc.ingredient2_id IN ({placeholders}))
               OR (dnc.ingredient1_id IN ({placeholders}) AND dnc.ingredient2_id IN ({placeholders}))
        """
        # Check both directions
        params = tuple(union_ingredients + union_ingredients)
        conflicts = self.db.execute_query(conflict_query, params)
        
        product1 = next(p for p in products if p['product_id'] == product1_id)
        product2 = next(p for p in products if p['product_id'] == product2_id)
        
        print(f"\nComparison: {product1['product_name']} vs {product2['product_name']}")
        print("=" * 70)
        
        if conflicts:
            print("\n⚠ INCOMPATIBILITIES DETECTED:")
            print("-" * 70)
            for c in conflicts:
                in_product1 = c['ingredient1_id'] in ing_set1 or c['ingredient2_id'] in ing_set1
                in_product2 = c['ingredient1_id'] in ing_set2 or c['ingredient2_id'] in ing_set2
                
                if in_product1 and in_product2:
                    print(f"  ✗ {c['ing1_name']} (ID: {c['ingredient1_id']}) <-> "
                          f"{c['ing2_name']} (ID: {c['ingredient2_id']})")
                    print(f"    Reason: {c['reason']}")
                    print(f"    Both ingredients appear in the union of both products")
        else:
            print("\n✓ No incompatibilities found in the union of ingredient sets")


