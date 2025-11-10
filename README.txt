DBMS Project - Inventory Management for Prepared/Frozen Meals Manufacturer
CSC540 - Project 1

Team Members:
[To be filled]

Project Structure:
- schema.sql: Contains all table definitions, constraints, triggers, and stored procedures
- data.sql: Contains INSERT statements for populating tables with sample data
- src/: Contains source code for the application (Java or Python)
- docs/: Contains documentation including ER diagram and project report

Compilation and Execution Instructions:

1. Database Setup (CHOOSE ONE METHOD):

   METHOD A - Using Python Setup Script (Recommended):
   - Update database credentials in setup_database.py
   - Run: python setup_database.py
   - This will automatically create database, load schema, and load data

   METHOD B - Using MySQL Command Line:
   - Create database: mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS csc_540;"
   - Load schema: mysql -u root -p csc_540 < schema.sql
   - Load data: mysql -u root -p csc_540 < data.sql

   METHOD C - Using MySQL Workbench:
   - Open schema.sql and execute it
   - Open data.sql and execute it

2. Application Execution:
   - Install Python 3.x and mysql-connector-python:
     pip install mysql-connector-python
   - Update database credentials in src/inventory_app.py
   - Run the application:
     python src/inventory_app.py
   - Or: python3 src/inventory_app.py

3. Testing Queries:
   - Option 1: Use the "View Queries" option in the application menu (option 4)
   - Option 2: Run queries.sql directly in MySQL
   - Option 3: Execute individual queries from queries.sql in MySQL Workbench

IMPORTANT: 
- schema.sql creates the database structure (tables, triggers, procedures, views)
- data.sql populates the database with sample data
- queries.sql contains the 5 required queries for reference/testing
- Always run schema.sql BEFORE data.sql

⚠️ SETUP ISSUES? See ERROR_EXPLANATION.md for error solutions
⚠️ RECOMMENDED: Use MySQL command line for setup (handles DELIMITER correctly)
   - Windows: Run setup.bat or use: mysql -u root -p csc_540 < schema.sql
   - See SETUP_INSTRUCTIONS.md for detailed setup instructions

Database Connection:
- DBMS: MariaDB/MySQL
- Default connection: localhost, database 'csc_540'
- Update credentials in src/inventory_app.py main() function:
  - host: 'localhost' (or your server address)
  - database: 'csc_540'
  - user: 'root' (or your database user)
  - password: '' (set your MySQL password)

Additional Notes:
- No ORM tools are used
- JDBC (Java) or Python menu-driven interface
- All constraints, triggers, and procedures are implemented in the database where possible



