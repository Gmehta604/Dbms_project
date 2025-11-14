#!/usr/bin/env python3
"""
Main CLI entry point for Meal Manufacturer System
"""

import sys
import os
from db_helper import DatabaseHelper
from manufacturer_menu import ManufacturerMenu
from supplier_menu import SupplierMenu
from viewer_menu import ViewerMenu
from queries_menu import QueriesMenu

def print_header():
    """Print application header"""
    print("=" * 70)
    print(" " * 15 + "MEAL MANUFACTURER SYSTEM")
    print("=" * 70)
    print()

def print_role_menu():
    """Print role selection menu"""
    print("Select Role:")
    print("  [1] Manufacturer")
    print("  [2] Supplier")
    print("  [3] General (Viewer)")
    print("  [4] View Queries")
    print("  [0] Exit")
    print()

def login(db: DatabaseHelper) -> dict:
    """
    Handle user login
    
    Returns:
        Authenticated user dictionary or None
    """
    print("=" * 70)
    print("LOGIN")
    print("=" * 70)
    print()
    
    username = input("Username: ").strip()
    if not username:
        print("✗ Username cannot be empty")
        return None
    
    password = input("Password: ").strip()
    if not password:
        print("✗ Password cannot be empty")
        return None
    
    # Debug: Check if username exists first
    check_query = "SELECT username FROM Users WHERE username = %s"
    username_check = db.execute_query(check_query, (username,))
    
    if not username_check:
        print(f"\n✗ Username '{username}' not found in database")
        return None
    
    user = db.authenticate_user(username, password)
    if user:
        print(f"\n✓ Welcome, {user.get('name', user['username'])}!")
        print(f"  Role: {user['role']}")
        if user.get('manufacturer_id'):
            print(f"  Manufacturer ID: {user['manufacturer_id']}")
        if user.get('supplier_id'):
            print(f"  Supplier ID: {user['supplier_id']}")
        print()
        return user
    else:
        print(f"\n✗ Invalid password for username '{username}'")
        print("  Please check your password and try again")
        return None

def main():
    """Main application entry point"""
    print_header()
    
    # Initialize database connection
    db = DatabaseHelper()
    if not db.connect():
        print("\n✗ Failed to connect to database. Exiting.")
        return 1
    
    try:
        while True:
            print_role_menu()
            choice = input("Enter choice: ").strip()
            print()
            
            if choice == '0':
                print("Thank you for using Meal Manufacturer System. Goodbye!")
                break
            
            elif choice == '1':
                # Manufacturer role
                user = login(db)
                if user and user['role'] == 'Manufacturer':
                    menu = ManufacturerMenu(db, user)
                    menu.run()
                elif user:
                    print(f"✗ User '{user['username']}' is not a Manufacturer")
                print()
            
            elif choice == '2':
                # Supplier role
                user = login(db)
                if user and user['role'] == 'Supplier':
                    menu = SupplierMenu(db, user)
                    menu.run()
                elif user:
                    print(f"✗ User '{user['username']}' is not a Supplier")
                print()
            
            elif choice == '3':
                # Viewer role
                user = login(db)
                if user and user['role'] == 'Viewer':
                    menu = ViewerMenu(db, user)
                    menu.run()
                elif user:
                    print(f"✗ User '{user['username']}' is not a Viewer")
                print()
            
            elif choice == '4':
                # View Queries (no login required)
                menu = QueriesMenu(db)
                menu.run()
                print()
            
            else:
                print("✗ Invalid choice. Please try again.")
                print()
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()
        print("\nConnection closed.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

