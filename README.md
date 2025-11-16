# **CSC540: Inventory Management Database Project**

This project implements the backend database (**schema**, **triggers**, and **stored procedures**) for an **inventory management system** built for a prepared-meals manufacturer.

---

## **👥 Project Team Members**

- JonCarlo Migaly, Gaurav Mehta, Shrawani Gulhane, Paul Nguyen

---

## **⚡ Quick Setup Instructions (For TAs/Instructors)**

To run this project independently, follow these steps:

### **Prerequisites**

- Python 3.13 or later
- MySQL Server (local or remote)
- Git (to clone the repository)

### **⚠️ Step 0: Start MySQL Server**

**Important:** MySQL must be running before you load the database. Choose your operating system:

**macOS (Homebrew):**

```bash
brew services start mysql
```

**macOS (Manual start):**

```bash
mysql.server start
```

**Linux:**

```bash
sudo systemctl start mysql
# or
sudo service mysql start
```

**Windows:**

```bash
net start MySQL80
# or use Services app to start "MySQL80"
```

**Verify MySQL is running:**

```bash
mysql -u root -p -e "SELECT 1;"
```

If you see `1` returned, MySQL is running! ✅

---

### **Setup Steps**

1. **Navigate to the project directory:**

   ```bash
   cd Dbms_project
   ```

2. **Create and activate the Python virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or for Windows:
   # venv\Scripts\activate
   ```

3. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Load the database schema and sample data:**

   ```bash
   cd Final_Project_Submissionfiles
   mysql -u root -p Meal_Manufacturer < Schema_procedures_triggers_combined.sql
   mysql -u root -p Meal_Manufacturer < data.sql
   cd ..
   ```

   (You will be prompted for your MySQL password)

5. **Run the application:**

   ```bash
   python main.py
   ```

6. **Login with test credentials (see Section II below)**

---

## **II. Demo Credentials**

| Role         | Username   | Password      | Notes                            |
| ------------ | ---------- | ------------- | -------------------------------- |
| Manufacturer | `jsmith`   | `password123` | Owns Product 100 (Steak Dinner)  |
| Supplier     | `jdoe`     | `password123` | Supplies Ingredients 201 and 104 |
| Viewer       | `bjohnson` | `password123` | Read-only user                   |

---

## **III. Key Functionality and Graded Features**

The final application is built on a **Transactional DBMS Layer** that enforces critical business rules before committing data.

### **1. Atomic Production and FEFO (Menu 3)**

The `create_product_batch` function demonstrates the entire process:

- **FEFO Logic (Python):** The app sorts available inventory by expiration date and auto-selects lots to consume.
- **Atomic Commit (DBMS):** It calls the `Record_Production_Batch` procedure, which uses a single TRANSACTION to guarantee that the creation, consumption, and cost calculation succeed simultaneously.

### **2. Health Risk and Rollback Block (Crucial Integrity Test)**

This test proves the database cannot be corrupted.

**Test Instructions:**

1. Log in as `jsmith` (Manufacturer),
2. Navigate to Menu → Run Reports → (Option 4: Conflicting ingredients)
3. Attempt to create a batch using Beef Steak (106) and Sodium Phosphate (104)

**Expected Result:** The procedure **rolls back** the transaction, and the app outputs:

```
ERROR: Health risk detected! Incompatible ingredients found in batch.
```

This proves `Evaluate_Health_Risk` is functional and prevents data corruption.

### **3. Traceability (Menu 4 / Report 4)**

**Conflicting Ingredients Report (Report 4):** This report demonstrates the complex flattening logic by successfully identifying the forbidden partner (104 Sodium Phosphate) for the items already consumed in the sample data, proving the data structure supports multi-level analysis.

---

## **📁 Project Structure**

```
.
├── sql_src/
│   ├── schema.sql                 # (1) All CREATE TABLE statements
│   ├── procedures_triggers.sql    # (2) All Triggers & Stored Procedures
│   └── test.sql                   # (4) TEST SCRIPT
│
├── Final_Project_Submissionfiles/
│   ├── Schema_procedures_triggers_combined.sql
│   └── data.sql
│
├── main.py                        # Python CLI application
├── requirements.txt               # Python packages
└── README.md                      # This file
```
