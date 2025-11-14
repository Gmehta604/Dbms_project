#!/usr/bin/env python3
"""
Database helper module for Meal Manufacturer CLI
Provides database connection and common operations
"""

import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, List, Tuple, Any
import getpass

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'Meal_Manufacturer',
    'user': 'root',
    'password': '',  # Will be set on connection
    'charset': 'utf8mb4',
    'autocommit': False
}

class DatabaseHelper:
    """Database connection and operation helper"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self, password: Optional[str] = None) -> bool:
        """
        Connect to the database
        
        Args:
            password: MySQL root password (if None, will prompt)
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            config = DB_CONFIG.copy()
            if password is not None:
                config['password'] = password
            elif not config['password']:
                config['password'] = getpass.getpass("Enter MySQL root password (press Enter if no password): ").strip()
            
            self.connection = mysql.connector.connect(**config)
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
            return True
        except Error as e:
            print(f"✗ Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results
        
        Args:
            query: SQL query string
            params: Optional parameters for parameterized query
        
        Returns:
            List of result dictionaries
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"✗ Query Error: {e}")
            return []
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> bool:
        """
        Execute an INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Optional parameters for parameterized query
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return True
        except Error as e:
            print(f"✗ Update Error: {e}")
            self.connection.rollback()
            return False
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """
        Execute a query multiple times with different parameters
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            return True
        except Error as e:
            print(f"✗ Batch Update Error: {e}")
            self.connection.rollback()
            return False
    
    def call_procedure(self, procedure_name: str, params: Optional[Tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Call a stored procedure
        
        Args:
            procedure_name: Name of the stored procedure
            params: Optional parameters
        
        Returns:
            Result set if any, None otherwise
        """
        try:
            if params:
                self.cursor.callproc(procedure_name, params)
            else:
                self.cursor.callproc(procedure_name)
            
            # Get results from all result sets
            results = []
            for result in self.cursor.stored_results():
                results.extend(result.fetchall())
            
            self.connection.commit()
            return results if results else None
        except Error as e:
            print(f"✗ Procedure Error: {e}")
            self.connection.rollback()
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user by username and password
        
        Args:
            username: Username
            password: Password
        
        Returns:
            User dictionary if authenticated, None otherwise
        """
        try:
            # Use BINARY comparison for exact password matching (case-sensitive)
            query = """
                SELECT u.user_id, u.username, u.role, u.name,
                       m.manufacturer_id, m.manufacturer_name,
                       s.supplier_id, s.supplier_name
                FROM Users u
                LEFT JOIN Manufacturers m ON u.user_id = m.user_id
                LEFT JOIN Suppliers s ON u.user_id = s.user_id
                WHERE u.username = %s AND BINARY u.password = %s
            """
            self.cursor.execute(query, (username, password))
            results = self.cursor.fetchall()
            return results[0] if results else None
        except Error as e:
            print(f"✗ Authentication error: {e}")
            return None
    
    def get_next_id(self, table: str, id_column: str) -> int:
        """
        Get the next available ID for a table
        
        Args:
            table: Table name
            id_column: ID column name
        
        Returns:
            Next available ID
        """
        query = f"SELECT COALESCE(MAX({id_column}), 0) + 1 AS next_id FROM {table}"
        results = self.execute_query(query)
        return results[0]['next_id'] if results else 1

