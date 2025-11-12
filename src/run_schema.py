#!/usr/bin/env python3
"""
Python script to execute schema.sql and create the Meal_Manufacturer database
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change this to your MySQL password
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

SCHEMA_FILE = os.path.join('sql_src', 'schema.sql')

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
        
        # Handle DELIMITER commands for stored procedures/triggers
        # Replace DELIMITER // with empty and restore at end
        delimiter_changed = False
        original_delimiter = ';'
        current_delimiter = ';'
        
        # Process DELIMITER commands
        lines = sql_script.split('\n')
        processed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip().upper()
            
            if stripped.startswith('DELIMITER'):
                # Extract new delimiter
                parts = line.split()
                if len(parts) > 1:
                    current_delimiter = parts[1]
                    delimiter_changed = True
                    print(f"  Changing delimiter to: {current_delimiter}")
                i += 1
                continue
            
            processed_lines.append(line)
            i += 1
        
        # If delimiter was changed, restore it at the end
        if delimiter_changed:
            processed_lines.append(f"DELIMITER {original_delimiter}")
        
        sql_script = '\n'.join(processed_lines)
        
        # Split into statements based on current delimiter
        # For simplicity, we'll use execute with multi=True for complex statements
        statements = []
        current_statement = ""
        
        for line in sql_script.split('\n'):
            stripped = line.strip()
            
            # Skip empty lines and single-line comments
            if not stripped:
                if current_statement:
                    current_statement += '\n'
                continue
            
            if stripped.startswith('--'):
                continue
            
            # Check for DELIMITER restoration
            if stripped.upper().startswith('DELIMITER') and ';' in stripped:
                current_delimiter = ';'
                continue
            
            current_statement += line + '\n'
            
            # Check if statement ends with current delimiter
            if stripped.endswith(current_delimiter):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # Execute each statement
        print(f"Executing {len(statements)} SQL statements...")
        print()
        
        for i, statement in enumerate(statements, 1):
            if not statement or statement.strip() == '':
                continue
            
            try:
                # Remove trailing delimiter for execution
                statement_clean = statement.rstrip().rstrip(current_delimiter).rstrip()
                
                if not statement_clean:
                    continue
                
                # Execute the statement
                # For complex statements (procedures, triggers), use execute with multi
                if any(keyword in statement_clean.upper() for keyword in ['CREATE PROCEDURE', 'CREATE TRIGGER', 'CREATE FUNCTION']):
                    # Execute multi-statement blocks
                    for result in cursor.execute(statement_clean, multi=True):
                        if result.with_rows:
                            result.fetchall()
                else:
                    # Execute single statement
                    cursor.execute(statement_clean)
                
                # Get description of what was executed
                statement_preview = statement_clean[:50].replace('\n', ' ')
                if len(statement_clean) > 50:
                    statement_preview += "..."
                
                print(f"✓ [{i}/{len(statements)}] Executed: {statement_preview}")
                
            except Error as e:
                # Some errors are expected (like "database already exists", "table already exists")
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ['exists', 'duplicate', 'already']):
                    statement_preview = statement[:50].replace('\n', ' ')
                    print(f"⚠ [{i}/{len(statements)}] {statement_preview} - {e}")
                else:
                    print(f"✗ [{i}/{len(statements)}] Error: {e}")
                    print(f"  Statement preview: {statement[:200]}...")
        
        print("\n✓ All statements processed!")
        return True
        
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
    print("Meal Manufacturer Database Schema Setup")
    print("=" * 60)
    print()
    
    # Check if schema.sql exists
    if not os.path.exists(SCHEMA_FILE):
        print(f"✗ Error: {SCHEMA_FILE} not found!")
        print(f"  Current directory: {os.getcwd()}")
        return False
    
    print(f"✓ Found {SCHEMA_FILE}")
    
    # Get password if not set
    if not DB_CONFIG['password']:
        password = input("Enter MySQL root password (press Enter if no password): ").strip()
        DB_CONFIG['password'] = password
    
    # Connect to MySQL server
    print("Connecting to MySQL server...")
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(buffered=True)
        print("✓ Connected to MySQL server successfully!")
        print()
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Check your username and password")
        print("3. Verify MySQL is installed and accessible")
        return False
    
    try:
        # Execute the schema file
        success = execute_sql_file(cursor, SCHEMA_FILE)
        
        if success:
            # Commit the changes
            connection.commit()
            print("\n✓ Database schema created successfully!")
            print("\nYou can now:")
            print("  - Connect to the database: mysql -u root -p Meal_Manufacturer")
            print("  - Or use MySQL Workbench to view the database")
        else:
            connection.rollback()
            print("\n✗ Failed to create database schema")
            return False
            
    except Exception as e:
        connection.rollback()
        print(f"\n✗ Error: {e}")
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

