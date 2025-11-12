#!/usr/bin/env python3
"""
Python script to execute data.sql and insert sample data into Meal_Manufacturer database
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'Meal_Manufacturer',  # Connect directly to the database
    'user': 'root',
    'password': '',  # Will prompt if empty
    'charset': 'utf8mb4'
}

def execute_sql_file(cursor, sql_file):
    """
    Execute SQL commands from a file
    
    Args:
        cursor: MySQL cursor object
        sql_file: Path to SQL file
    """
    try:
        # Read the SQL file
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Split by semicolon to get individual statements
        # Filter out empty statements and comments
        statements = []
        current_statement = ""
        
        for line in sql_script.split('\n'):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                if current_statement:
                    current_statement += '\n'
                continue
            
            # Skip comment-only lines
            if stripped.startswith('--'):
                continue
            
            current_statement += line + '\n'
            
            # If line ends with semicolon, it's the end of a statement
            if stripped.endswith(';'):
                stmt = current_statement.strip()
                if stmt and not stmt.startswith('--'):
                    statements.append(stmt)
                current_statement = ""
        
        # Execute each statement
        print(f"Found {len(statements)} SQL statements to execute...")
        print()
        
        success_count = 0
        warning_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
            
            # Skip USE statements as we're already connected to the database
            if 'USE' in statement.upper():
                continue
            
            try:
                # Execute the statement
                cursor.execute(statement)
                
                # Consume any results to prevent "Commands out of sync" error
                # Only fetch if there are results
                try:
                    if cursor.with_rows:
                        cursor.fetchall()
                    # Check for additional result sets
                    while cursor.nextset():
                        if cursor.with_rows:
                            cursor.fetchall()
                except:
                    # No results to fetch, that's fine - cursor is already in sync
                    pass
                
                success_count += 1
                
                # Show progress with more detail
                statement_type = "Statement"
                
                if 'INSERT INTO' in statement.upper():
                    # Extract table name
                    parts = statement.upper().split()
                    for j, part in enumerate(parts):
                        if part == 'INTO' and j + 1 < len(parts):
                            table_name = parts[j + 1]
                            statement_type = f"Insert into {table_name}"
                            break
                elif 'UPDATE' in statement.upper():
                    parts = statement.upper().split()
                    if len(parts) > 1:
                        statement_type = f"Update {parts[1]}"
                elif 'ALTER TABLE' in statement.upper():
                    parts = statement.upper().split()
                    for j, part in enumerate(parts):
                        if part == 'TABLE' and j + 1 < len(parts):
                            statement_type = f"Alter {parts[j + 1]}"
                            break
                
                print(f"✓ [{i}/{len(statements)}] {statement_type}")
                
            except Error as e:
                error_msg = str(e).lower()
                
                # Reset cursor if it's out of sync
                try:
                    # Try to consume any pending results
                    if cursor.with_rows:
                        cursor.fetchall()
                    while cursor.nextset():
                        if cursor.with_rows:
                            cursor.fetchall()
                except:
                    # If cursor is really out of sync, we need to reset it
                    try:
                        cursor.reset()
                    except:
                        pass
                
                # Some errors are expected (like "already exists", "duplicate entry")
                if any(keyword in error_msg for keyword in ['exists', 'duplicate', 'already']):
                    warning_count += 1
                    stmt_preview = statement.replace('\n', ' ')[:50]
                    print(f"⚠ [{i}/{len(statements)}] {stmt_preview}... - {e}")
                else:
                    error_count += 1
                    print(f"✗ [{i}/{len(statements)}] Error: {e}")
                    # Show first 100 chars of the statement
                    stmt_preview = statement.replace('\n', ' ')[:100]
                    print(f"   Statement: {stmt_preview}...")
                    # Don't stop on errors, continue with other statements
        
        print()
        print("=" * 60)
        print(f"Summary: {success_count} successful, {warning_count} warnings, {error_count} errors")
        print("=" * 60)
        
        return error_count == 0
        
    except FileNotFoundError:
        print(f"✗ Error: File '{sql_file}' not found!")
        return False
    except Error as e:
        print(f"✗ Database Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Meal Manufacturer Database - Sample Data Insertion")
    print("=" * 60)
    print()
    
    # Check if data.sql exists
    sql_file = "sql_src/data.sql"
    if not os.path.exists(sql_file):
        print(f"✗ Error: {sql_file} not found in current directory!")
        print(f"  Current directory: {os.getcwd()}")
        return False
    
    print(f"✓ Found {sql_file}")
    
    # Get password if not set
    if not DB_CONFIG['password']:
        password = input("Enter MySQL root password (press Enter if no password): ").strip()
        DB_CONFIG['password'] = password
    
    # Connect to MySQL server and database
    print("\nConnecting to MySQL server and database...")
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        # Use buffered cursor to prevent "Commands out of sync" errors
        cursor = connection.cursor(buffered=True)
        print("✓ Connected to MySQL server and 'Meal_Manufacturer' database successfully!")
        print()
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Make sure the database 'Meal_Manufacturer' exists (run schema.sql first)")
        print("3. Check your username and password")
        print("4. Verify MySQL is installed and accessible")
        print("5. Install mysql-connector-python: pip install mysql-connector-python")
        return False
    
    try:
        # Execute the data file
        success = execute_sql_file(cursor, sql_file)
        
        if success:
            # Commit the changes
            connection.commit()
            print("\n✓ Sample data inserted successfully!")
            print("\nData inserted:")
            print("  - Users (Manufacturers, Suppliers, Viewers)")
            print("  - Categories and Products")
            print("  - Ingredients and Compositions")
            print("  - Suppliers and Formulations")
            print("  - Ingredient Batches")
            print("  - Recipe Plans and Ingredients")
            print("  - Product Batches")
            print("  - Batch Consumption records")
            print("  - Conflict Pairs")
            print("\nYou can now query the database to verify the data.")
        else:
            print("\n⚠ Some errors occurred. Check the output above.")
            print("Note: Some warnings (like 'already exists') are normal if running multiple times.")
            response = input("\nDo you want to commit the successful inserts? (y/n): ").strip().lower()
            if response == 'y':
                try:
                    # Close and recreate cursor to ensure it's in sync before commit
                    cursor.close()
                    cursor = connection.cursor(buffered=True)
                    connection.commit()
                    print("✓ Changes committed.")
                except Error as e:
                    print(f"⚠ Could not commit: {e}")
            else:
                try:
                    # Close and recreate cursor to ensure it's in sync before rollback
                    cursor.close()
                    cursor = connection.cursor(buffered=True)
                    connection.rollback()
                    print("✗ Changes rolled back.")
                except Error as e:
                    print(f"⚠ Could not rollback: {e}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        try:
            # Try to rollback, but recreate cursor first if needed
            try:
                connection.rollback()
            except:
                # If rollback fails, cursor might be out of sync, recreate it
                cursor.close()
                cursor = connection.cursor(buffered=True)
                connection.rollback()
        except:
            pass  # Ignore rollback errors if connection is already closed
        return False
        
    finally:
        # Close connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print("\nConnection closed.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)

