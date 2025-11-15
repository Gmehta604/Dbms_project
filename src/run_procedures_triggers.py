#!/usr/bin/env python3
"""
Python script to execute procedures_triggers.sql
"""

import mysql.connector
from mysql.connector import Error
import sys
import os
import getpass

# Database connection configuration
DB_CONFIG = {
    'unix_socket': '/tmp/mysql.sock',
    'database': 'Meal_Manufacturer',
    'user': 'root',
    'password': '',
    'charset': 'utf8mb4'
}

def execute_sql_file(cursor, sql_file):
    """Execute SQL commands from a file"""
    try:
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Split by delimiter changes and semicolons
        statements = []
        current_statement = ""
        delimiter = ';'
        
        for line in sql_script.split('\n'):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('--'):
                continue
            
            # Handle delimiter changes
            if stripped.upper().startswith('DELIMITER'):
                parts = stripped.split()
                if len(parts) > 1:
                    delimiter = parts[1]
                continue
            
            current_statement += line + '\n'
            
            # Check if statement ends with current delimiter
            if stripped.endswith(delimiter):
                stmt = current_statement.strip()
                if stmt and not stmt.startswith('--'):
                    # Remove delimiter from end
                    stmt = stmt[:-len(delimiter)].strip()
                    statements.append(stmt)
                current_statement = ""
        
        # Execute each statement
        print(f"Found {len(statements)} SQL statements to execute...")
        print()
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
            
            # Skip USE statements (we're already connected to the database)
            if 'USE' in statement.upper():
                success_count += 1
                print(f"⊘ [{i}/{len(statements)}] USE statement (skipped - already connected)")
                continue
            
            try:
                # Execute statement directly (we've already parsed by delimiter)
                cursor.execute(statement)
                
                # Consume any results
                try:
                    if cursor.with_rows:
                        cursor.fetchall()
                    # Check for additional result sets
                    while cursor.nextset():
                        if cursor.with_rows:
                            cursor.fetchall()
                except:
                    pass  # No results to fetch, that's fine
                
                success_count += 1
                print(f"✓ [{i}/{len(statements)}] Statement executed")
                
            except Error as e:
                error_count += 1
                print(f"✗ [{i}/{len(statements)}] Error: {e}")
                stmt_preview = statement.replace('\n', ' ')[:100]
                print(f"   Statement: {stmt_preview}...")
        
        print()
        print("=" * 60)
        print(f"Summary: {success_count} successful, {error_count} errors")
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
    print("Meal Manufacturer Database - Procedures & Triggers")
    print("=" * 60)
    print()
    
    sql_file = "sql_src/procedures_triggers.sql"
    if not os.path.exists(sql_file):
        print(f"✗ Error: {sql_file} not found!")
        print(f"  Current directory: {os.getcwd()}")
        return False
    
    print(f"✓ Found {sql_file}")
    
    if not DB_CONFIG['password']:
        password = getpass.getpass("Enter MySQL root password (press Enter if no password): ").strip()
        DB_CONFIG['password'] = password
    
    print("\nConnecting to MySQL server and database...")
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        # Use unbuffered cursor for multi-statement execution
        cursor = connection.cursor()
        print("✓ Connected successfully!")
        print()
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        return False
    
    try:
        success = execute_sql_file(cursor, sql_file)
        
        if success:
            connection.commit()
            print("\n✓ Procedures and triggers created successfully!")
        else:
            print("\n⚠ Some errors occurred. Check the output above.")
            response = input("\nDo you want to commit successful operations? (y/n): ").strip().lower()
            if response == 'y':
                connection.commit()
                print("✓ Changes committed.")
            else:
                connection.rollback()
                print("✗ Changes rolled back.")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        connection.rollback()
        return False
        
    finally:
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


