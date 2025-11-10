#!/usr/bin/env python3
"""
Database Setup Script for CSC540 Project 1
This script creates the database schema and loads sample data.
"""

import mysql.connector
from mysql.connector import Error
import os
import sys

def read_sql_file(file_path):
    """Read SQL file and return its contents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found!")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def execute_sql_script(connection, sql_script, file_name):
    """Execute SQL script with proper error handling"""
    cursor = connection.cursor()
    
    # Split script into individual statements
    # Remove comments and empty lines, then split by semicolon
    statements = []
    current_statement = []
    
    for line in sql_script.split('\n'):
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith('--') or line.startswith('/*'):
            continue
        
        # Skip USE statements as we're already connected to the database
        if line.upper().startswith('USE '):
            continue
        
        current_statement.append(line)
        
        # If line ends with semicolon, we have a complete statement
        if line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement.strip() and statement.strip() != ';':
                statements.append(statement)
            current_statement = []
    
    # Execute each statement
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        try:
            cursor.execute(statement)
            success_count += 1
            if i % 10 == 0:  # Progress indicator
                print(f"  Executed {i} statements...")
        except Error as e:
            error_count += 1
            print(f"  Error in statement {i}: {e}")
            print(f"  Statement: {statement[:100]}...")
            # Continue with next statement instead of stopping
            continue
    
    connection.commit()
    cursor.close()
    
    print(f"  Completed: {success_count} statements executed successfully")
    if error_count > 0:
        print(f"  Warnings: {error_count} statements had errors")
    
    return success_count, error_count

def main():
    """Main setup function"""
    # Database connection parameters
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'Gaurav$01062002',  # Update with your password
        'database': 'csc_540'  # Update with your database name
    }
    
    print("="*60)
    print("CSC540 Project 1 - Database Setup")
    print("="*60)
    
    # Step 1: Connect to MySQL (without database first to create it)
    print("\nStep 1: Connecting to MySQL server...")
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        
        if connection.is_connected():
            print("  ✓ Connected to MySQL server")
            
            # Create database if it doesn't exist
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            print(f"  ✓ Database '{DB_CONFIG['database']}' ready")
            cursor.close()
            connection.close()
        else:
            print("  ✗ Failed to connect to MySQL server")
            sys.exit(1)
            
    except Error as e:
        print(f"  ✗ Error connecting to MySQL: {e}")
        print("\nPlease check:")
        print("  1. MySQL/MariaDB is running")
        print("  2. Username and password are correct")
        print("  3. Database credentials in this script are updated")
        sys.exit(1)
    
    # Step 2: Connect to the database
    print(f"\nStep 2: Connecting to database '{DB_CONFIG['database']}'...")
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print("  ✓ Connected to database")
        else:
            print("  ✗ Failed to connect to database")
            sys.exit(1)
            
    except Error as e:
        print(f"  ✗ Error connecting to database: {e}")
        sys.exit(1)
    
    # Step 3: Load schema.sql
    print("\nStep 3: Loading database schema (schema.sql)...")
    schema_file = 'schema.sql'
    
    if not os.path.exists(schema_file):
        print(f"  ✗ Error: {schema_file} not found in current directory")
        print(f"  Current directory: {os.getcwd()}")
        connection.close()
        sys.exit(1)
    
    schema_sql = read_sql_file(schema_file)
    if schema_sql:
        execute_sql_script(connection, schema_sql, schema_file)
        print("  ✓ Schema loaded successfully")
    else:
        connection.close()
        sys.exit(1)
    
    # Step 4: Load data.sql
    print("\nStep 4: Loading sample data (data.sql)...")
    data_file = 'data.sql'
    
    if not os.path.exists(data_file):
        print(f"  ✗ Error: {data_file} not found in current directory")
        connection.close()
        sys.exit(1)
    
    data_sql = read_sql_file(data_file)
    if data_sql:
        execute_sql_script(connection, data_sql, data_file)
        print("  ✓ Sample data loaded successfully")
    else:
        connection.close()
        sys.exit(1)
    
    # Step 5: Verify installation
    print("\nStep 5: Verifying installation...")
    try:
        cursor = connection.cursor()
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"  ✓ Found {len(tables)} tables")
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM USERS")
        user_count = cursor.fetchone()[0]
        print(f"  ✓ Found {user_count} users")
        
        # Check products
        cursor.execute("SELECT COUNT(*) FROM PRODUCTS")
        product_count = cursor.fetchone()[0]
        print(f"  ✓ Found {product_count} products")
        
        cursor.close()
        
    except Error as e:
        print(f"  ⚠ Warning: Could not verify installation: {e}")
    
    # Close connection
    connection.close()
    
    print("\n" + "="*60)
    print("Database setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run the application: python src/inventory_app.py")
    print("2. Test queries: Run queries.sql in MySQL or use the app's query viewer")
    print("3. Login with sample credentials:")
    print("   - Manufacturer: mfg001_user / password123")
    print("   - Supplier: supplier21_user / password123")
    print("   - Viewer: viewer1 / password123")

if __name__ == '__main__':
    main()

