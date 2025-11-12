#!/usr/bin/env python3
"""
Simple Python script to execute schema.sql and create the Meal_Manufacturer database
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
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
            
            try:
                # Execute the statement
                cursor.execute(statement)
                success_count += 1
                
                # Show progress
                statement_type = "Unknown"
                if 'CREATE DATABASE' in statement.upper():
                    statement_type = "Database"
                elif 'CREATE TABLE' in statement.upper():
                    # Extract table name
                    parts = statement.split()
                    for j, part in enumerate(parts):
                        if part.upper() == 'TABLE':
                            if j + 1 < len(parts):
                                statement_type = f"Table: {parts[j+1]}"
                                break
                elif 'ALTER TABLE' in statement.upper():
                    statement_type = "Constraint"
                
                print(f"✓ [{i}/{len(statements)}] {statement_type}")
                
            except Error as e:
                error_msg = str(e).lower()
                # Some errors are expected (like "database already exists")
                if any(keyword in error_msg for keyword in ['exists', 'duplicate', 'already']):
                    warning_count += 1
                    print(f"⚠ [{i}/{len(statements)}] Already exists (skipped)")
                else:
                    error_count += 1
                    print(f"✗ [{i}/{len(statements)}] Error: {e}")
                    # Show first 100 chars of the statement
                    stmt_preview = statement.replace('\n', ' ')[:100]
                    print(f"   Statement: {stmt_preview}...")
        
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
    print("Meal Manufacturer Database Schema Setup")
    print("=" * 60)
    print()
    
    # Check if schema.sql exists
    sql_file = "sql_src/schema.sql"
    if not os.path.exists(sql_file):
        print(f"✗ Error: {sql_file} not found in current directory!")
        print(f"  Current directory: {os.getcwd()}")
        return False
    
    print(f"✓ Found {sql_file}")
    
    # Get password if not set
    if not DB_CONFIG['password']:
        password = input("Enter MySQL root password (press Enter if no password): ").strip()
        DB_CONFIG['password'] = password
    
    # Connect to MySQL server
    print("\nConnecting to MySQL server...")
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✓ Connected to MySQL server successfully!")
        print()
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Check your username and password")
        print("3. Verify MySQL is installed and accessible")
        print("4. Install mysql-connector-python: pip install mysql-connector-python")
        return False
    
    try:
        # Execute the schema file
        success = execute_sql_file(cursor, sql_file)
        
        if success:
            # Commit the changes
            connection.commit()
            print("\n✓ Database schema created successfully!")
            print("\nNext steps:")
            print("  - Connect to database: mysql -u root -p Meal_Manufacturer")
            print("  - Or use MySQL Workbench to view the database")
        else:
            connection.rollback()
            print("\n⚠ Some errors occurred. Check the output above.")
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

