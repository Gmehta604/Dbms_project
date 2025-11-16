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
            SELECT p.product_id, p.name AS product_name,
                   m.name AS manufacturer_name, c.name AS category_name, 
                   p.standard_batch_size
            FROM Product p
            JOIN Manufacturer m ON p.manufacturer_id = m.manufacturer_id
            JOIN Category c ON p.category_id = c.category_id
            ORDER BY m.name, c.name, p.name
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
            print(f"        Batch Size: {p['standard_batch_size']} units")
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
            SELECT p.product_id, p.name AS product_name, m.name AS manufacturer_name
            FROM Product p
            JOIN Manufacturer m ON p.manufacturer_id = m.manufacturer_id
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
        if product_id not in [str(p['product_id']) for p in products]:
            print("✗ Invalid product ID")
            return
        
        # Get active recipe
        recipe_query = """
            SELECT recipe_id, name
            FROM Recipe
            WHERE product_id = %s AND is_active = TRUE
            ORDER BY creation_date DESC
            LIMIT 1
        """
        recipes = self.db.execute_query(recipe_query, (product_id,))
        
        if not recipes:
            print("✗ No active recipe found for this product")
            return
        
        recipe_id = recipes[0]['recipe_id']
        
        # Get recipe ingredients and flatten compounds (via FormulationMaterials)
        query = """
            SELECT 
                COALESCE(fm.material_ingredient_id, ri.ingredient_id) AS ingredient_id,
                COALESCE(mi.name, i.name) AS ingredient_name,
                SUM(ri.quantity * COALESCE(fm.quantity, 1)) AS total_quantity
            FROM RecipeIngredient ri
            JOIN Ingredient i ON ri.ingredient_id = i.ingredient_id
            LEFT JOIN Formulation f ON ri.ingredient_id = f.ingredient_id 
                AND (f.valid_to_date IS NULL OR f.valid_to_date >= CURDATE())
            LEFT JOIN FormulationMaterials fm ON f.formulation_id = fm.formulation_id
            LEFT JOIN Ingredient mi ON fm.material_ingredient_id = mi.ingredient_id
            WHERE ri.recipe_id = %s
            GROUP BY ingredient_id, ingredient_name
            ORDER BY total_quantity DESC
        """
        ingredients = self.db.execute_query(query, (recipe_id,))
        
        if not ingredients:
            print("No ingredients found")
            return
        
        product = next(p for p in products if str(p['product_id']) == product_id)
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
            SELECT p.product_id, p.name AS product_name, m.name AS manufacturer_name
            FROM Product p
            JOIN Manufacturer m ON p.manufacturer_id = m.manufacturer_id
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
        if product1_id not in [str(p['product_id']) for p in products]:
            print("✗ Invalid product ID")
            return
        
        product2_id = input("Product 2 ID: ").strip()
        if product2_id not in [str(p['product_id']) for p in products]:
            print("✗ Invalid product ID")
            return
        
        if product1_id == product2_id:
            print("✗ Cannot compare product with itself")
            return
        
        # Get flattened ingredient sets for both products
        def get_flattened_ingredients(prod_id):
            recipe_query = """
                SELECT recipe_id FROM Recipe
                WHERE product_id = %s AND is_active = TRUE
                ORDER BY creation_date DESC LIMIT 1
            """
            recipes = self.db.execute_query(recipe_query, (prod_id,))
            if not recipes:
                return set()
            
            recipe_id = recipes[0]['recipe_id']
            query = """
                SELECT DISTINCT COALESCE(fm.material_ingredient_id, ri.ingredient_id) AS ingredient_id
                FROM RecipeIngredient ri
                JOIN Ingredient i ON ri.ingredient_id = i.ingredient_id
                LEFT JOIN Formulation f ON ri.ingredient_id = f.ingredient_id 
                    AND (f.valid_to_date IS NULL OR f.valid_to_date >= CURDATE())
                LEFT JOIN FormulationMaterials fm ON f.formulation_id = fm.formulation_id
                WHERE ri.recipe_id = %s
            """
            results = self.db.execute_query(query, (recipe_id,))
            return set(r['ingredient_id'] for r in results if r['ingredient_id'])
        
        ing_set1 = get_flattened_ingredients(product1_id)
        ing_set2 = get_flattened_ingredients(product2_id)
        
        if not ing_set1 or not ing_set2:
            print("✗ One or both products have no active recipes")
            return
        
        # Check for conflicts in the union
        union_ingredients = list(ing_set1 | ing_set2)
        
        if not union_ingredients:
            print("No ingredients to compare")
            return
        
        # Check for do-not-combine pairs
        placeholders = ','.join(['%s'] * len(union_ingredients))
        conflict_query = f"""
            SELECT DISTINCT dnc.ingredient_a_id, dnc.ingredient_b_id,
                   i1.name AS ing_a_name, i2.name AS ing_b_name
            FROM DoNotCombine dnc
            JOIN Ingredient i1 ON dnc.ingredient_a_id = i1.ingredient_id
            JOIN Ingredient i2 ON dnc.ingredient_b_id = i2.ingredient_id
            WHERE (dnc.ingredient_a_id IN ({placeholders}) AND dnc.ingredient_b_id IN ({placeholders}))
        """
        conflicts = self.db.execute_query(conflict_query, tuple(union_ingredients + union_ingredients))
        
        product1 = next(p for p in products if str(p['product_id']) == product1_id)
        product2 = next(p for p in products if str(p['product_id']) == product2_id)
        
        print(f"\nComparison: {product1['product_name']} vs {product2['product_name']}")
        print("=" * 70)
        
        if conflicts:
            print("\n⚠ INCOMPATIBILITIES DETECTED:")
            print("-" * 70)
            for c in conflicts:
                in_product1 = c['ingredient_a_id'] in ing_set1 or c['ingredient_b_id'] in ing_set1
                in_product2 = c['ingredient_a_id'] in ing_set2 or c['ingredient_b_id'] in ing_set2
                
                if in_product1 and in_product2:
                    print(f"  ✗ {c['ing_a_name']} (ID: {c['ingredient_a_id']}) <-> "
                          f"{c['ing_b_name']} (ID: {c['ingredient_b_id']})")
                    print(f"    Both ingredients appear in the union of both products")
        else:
            print("\n✓ No incompatibilities found in the union of ingredient sets")



