# **CSC540: Inventory Management Database Project**

This project implements the backend database (**schema**, **triggers**, and **stored procedures**) for an **inventory management system** built for a prepared-meals manufacturer.

This README serves as the **owner’s manual** for the **application development team**.

---

## **📁 Project Structure**

```
.
├── sql_src/
│   ├── schema.sql                 # (1) All CREATE TABLE statements
│   ├── procedures_triggers.sql    # (2) All Triggers & Stored Procedures
│   ├── populate.sql               # (3) Sample data
│   └── test.sql                   # (4) MASTER BUILD & TEST SCRIPT
│
├── main.py                        # (To be built by App Team)
├── requirements.txt               # Python packages
└── README.md                      # This file
```

---

# **1. 🚀 Quick Start: Build & Test the Database**

Follow these steps to get a complete, working, populated database on your machine.

---

## **Prerequisites**

- Python 3.x
- MySQL or MariaDB server (local)

---

## **Step 1: Python Virtual Environment**

This project uses a `venv` to manage dependencies.

```bash
# 1. Create the virtual environment
python3 -m venv venv

# 2. Activate it
# macOS / Linux:
source venv/bin/activate

# Windows:
# .\venv\Scripts\activate

# 3. Install required packages
pip install -r requirements.txt
```

---

## **Step 2: Database Configuration**

The project assumes a **local MySQL server** using user `root`.

- If your MySQL user requires a password, you’ll be prompted.
- If you use a different MySQL user, edit the `-u root` part of the command in **Step 3** or modify `sql_src/test.sql`.

---

## **Step 3: Build & Test the Database (One-Button Build)**

You **do not** need to run `.sql` files manually.
The script **test.sql** handles everything.

Run:

```bash
mysql -v -u root -p Meal_Manufacturer < sql_src/test.sql
```

You will be prompted for your MySQL password.

### ✔️ This command will:

1. DROP the `Meal_Manufacturer` database (if it already exists)
2. CREATE a fresh `Meal_Manufacturer` database
3. BUILD the schema (`schema.sql`)
4. BUILD all logic (`procedures_triggers.sql`)
5. POPULATE the tables (`populate.sql`)
6. RUN all tests

After this runs, you’ll have a **fully-tested database**, ready for integration.

---

# **2. 🧠 Database “API” Guide (For App Developers)**

The backend is intentionally **smart**.
Your Python code **does not** manually update inventory or generate lot numbers — the **database handles that automatically**.

---

## **🔥 Automatic Triggers (Things You _Do Not_ Code in Python)**

### **1. Lot Number Creation**

**You do:**
`INSERT` into `IngredientBatch` or `ProductBatch`.

**Database does:**
`trg_compute_product_lot_number` auto-builds the `lot_number` PK
(e.g., `100-MFG001-B0901`).

---

### **2. Validation**

**You do:**
Insert into `BatchConsumption`.

**Database does:**
`trg_validate_consumption` checks:

- Expiration violations
- Over-consumption (more than `quantity_on_hand`)

On failure → raises `mysql.connector.Error`.

---

### **3. Inventory Management**

**Consumption:**

- Insert into `BatchConsumption`
- `trg_maintain_on_hand_CONSUME` automatically subtracts inventory

**Undo consumption:**

- Delete from `BatchConsumption`
- `trg_maintain_on_hand_ADJUST` automatically restores inventory

---

## **🎛️ Stored Procedures (What You _Do_ Call From Python)**

---

### ### **1. `Record_Production_Batch` — The "Engine"**

Atomic, all-or-nothing creation of a production batch.

**Python call:**

```python
cursor.callproc('Record_Production_Batch', args)
```

**Arguments (tuple format):**

| Param                     | Example        | Description                 |
| ------------------------- | -------------- | --------------------------- |
| `p_product_id`            | `'100'`        | Product ID                  |
| `p_manufacturer_id`       | `'MFG001'`     | Manufacturer                |
| `p_manufacturer_batch_id` | `'B0902'`      | New batch ID                |
| `p_produced_quantity`     | `100`          | Units produced              |
| `p_expiration_date`       | `'2026-12-01'` | Batch expiration            |
| `p_recipe_id_used`        | `1`            | Recipe used                 |
| `p_consumption_list`      | JSON string    | FEFO-based consumption plan |

**On success:** commits
**On failure:** rolls back, raises `mysql.connector.Error`

---

### **2. `Trace_Recall` — The "Search"**

Returns all product batches affected by an ingredient recall.

**Python call:**

```python
cursor.callproc('Trace_Recall', args)
```

**Params:**

- `p_ingredient_lot_number`
- `p_recall_date`

Fetch results via `cursor.stored_results()`.

---

### **3. `Evaluate_Health_Risk`**

You **do not** call this — the database calls it internally.

---

# **3. 🧩 App Dev Team: Your Main Task**

Your major job is to implement the **Create Product Batch** workflow in Python.

This workflow prepares the JSON input for `Record_Production_Batch`.

---

## **🛠️ “Create Product Batch” Workflow (Python)**

### **1. Get Input**

- Ask user for `product_id`
- Ask for `produced_quantity`

---

### **2. Validate Quantity**

Query `Product.standard_batch_size`.
Check:

```python
produced_quantity % standard_batch_size == 0
```

---

### **3. Get Recipe**

Query `RecipeIngredient` for the product’s recipe.

---

### **4. Calculate Total Ingredient Needs**

Compute total raw materials required:

Example:

- Beef `'106'`: `600 oz`
- Seasoning `'201'`: `20 oz`

---

### **5. Run FEFO Selection**

For each ingredient:

1. Query `IngredientBatch` ordered by expiration ascending
2. Auto-allocate lots until requirement met
3. If not enough stock → stop and inform user

---

### **6. Build the JSON Consumption Plan**

```python
consumption_plan = [
    {"lot": "106-20-B0005", "qty": 600},
    {"lot": "201-20-B0001", "qty": 20}
]
json_string = json.dumps(consumption_plan)
```

---

### **7. Call the Procedure**

Build your args tuple and:

```python
try:
    cursor.callproc('Record_Production_Batch', args)
except mysql.connector.Error as e:
    # handle DB error
```

---

# **✔️ Done!**

Let me know if you'd like:

- A prettier version with badges & logos
- A collapsible-section version
- A GitHub-flavored table of contents
- Auto-generated ERD diagrams
- ASCII art logos for your README

Happy building! 🚀
