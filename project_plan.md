````markdown
# **Project Plan (Phase 2): From Database to Final Application**

The database engine is complete, tested, and documented in `README.md`.

This plan outlines the remaining tasks for the application team to build the Python CLI and prepare the final submission materials.

---

## **Task 1: Build the Python Application (CLI)**

The goal: create a menu-driven Python application (`main.py`) using `mysql-connector-python` to interact with the database.

### **1.1. Build the Main Shell & Connection**
- Create `main.py` (already done in scaffold)
- Implement Login Screen (already done)
- Implement Role Selection Menu (already done)

---

### **1.2. Implement the “Simple” Functions**

These rely on **simple SELECT/INSERT** queries and on **triggers handling the heavy lifting**.

#### **Supplier Menu (role = 'Supplier')**
- **Manage Ingredients Supplied:** UI for INSERT/UPDATE on `Formulation`
- **Create Ingredient Batch:** UI for INSERT into `IngredientBatch`  
  *(Triggers handle lot number, validation, inventory logic.)*

#### **Manufacturer Menu (role = 'Manufacturer')**
- **Create & Manage Product Types:** INSERT/UPDATE on `Product`
- **Create & Update Recipe Plans:** INSERT on `Recipe` and `RecipeIngredient`

#### **Viewer Menu (role = 'Viewer')**
- **Browse Product Types:** SELECT join on `Product`, `Category`, `Manufacturer`
- **Generate Ingredient List:** complex SELECT (see `README.md`)

---

### **1.3. Implement the “Boss Level” Function**
#### **Create Product Batch (for Manufacturer role)**  
This is the most complex workflow — *assigned to Teammate 1.*

Your `README.md` (Section 3) contains the 7-step process.

The `main.py` scaffold already has **~90%** of the logic.

---

## **Task 2: Implement the 5 Required Queries**  
*(Assigned to Teammate 2 — lives inside `run_manufacturer_reports()`)*

Starter SQL for each required query:

---

### **1. Last batch of product type Steak Dinner (100) from MFG001**
```sql
SELECT
    bc.ingredient_lot_number,
    i.name
FROM ProductBatch pb
JOIN BatchConsumption bc ON pb.lot_number = bc.product_lot_number
JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
WHERE pb.product_id = '100'
  AND pb.manufacturer_id = 'MFG001'
ORDER BY pb.production_date DESC
LIMIT 1;
````

---

### **2. For MFG002: suppliers they purchased from + total money spent**

```sql
SELECT
    s.name AS supplier_name,
    SUM(bc.quantity_consumed * ib.per_unit_cost) AS total_spent
FROM BatchConsumption bc
JOIN ProductBatch pb ON bc.product_lot_number = pb.lot_number
JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
JOIN Supplier s ON ib.supplier_id = s.supplier_id
WHERE pb.manufacturer_id = 'MFG002'
GROUP BY s.supplier_id, s.name;
```

---

### **3. Unit cost of product lot 100-MFG001-B0901**

```sql
SELECT
    (total_batch_cost / produced_quantity) AS unit_cost
FROM ProductBatch
WHERE lot_number = '100-MFG001-B0901';
```

---

### **4. Ingredients that cannot be included (health-risk conflicts)**

This uses the logic from `Evaluate_Health_Risk`:

```sql
CREATE TEMPORARY TABLE Temp_Atoms_In_Batch AS (
    -- Populate with all atomic ingredients in lot '100-MFG001-B0901'
    -- ... (flattening logic from Evaluate_Health_Risk)
);

SELECT
    i.ingredient_id,
    i.name AS conflicting_ingredient
FROM Ingredient i
JOIN DoNotCombine dnc ON i.ingredient_id = dnc.ingredient_a_id
JOIN Temp_Atoms_In_Batch t ON dnc.ingredient_b_id = t.ingredient_id
WHERE i.ingredient_id NOT IN (SELECT ingredient_id FROM Temp_Atoms_In_Batch)

UNION

SELECT
    i.ingredient_id,
    i.name AS conflicting_ingredient
FROM Ingredient i
JOIN DoNotCombine dnc ON i.ingredient_id = dnc.ingredient_b_id
JOIN Temp_Atoms_In_Batch t ON dnc.ingredient_a_id = t.ingredient_id
WHERE i.ingredient_id NOT IN (SELECT ingredient_id FROM Temp_Atoms_In_Batch);
```

---

### **5. Manufacturers that supplier James Miller (21) has *not* supplied**

```sql
SELECT m.manufacturer_id, m.name
FROM Manufacturer m
WHERE m.manufacturer_id NOT IN (
    SELECT DISTINCT pb.manufacturer_id
    FROM BatchConsumption bc
    JOIN IngredientBatch ib ON bc.ingredient_lot_number = ib.lot_number
    JOIN ProductBatch pb ON bc.product_lot_number = pb.lot_number
    WHERE ib.supplier_id = '21'
);
```

---

## **Task 3: Final Report (35% of Grade)**

*(Assigned to Person 1 / DBA)*

Required components:

### **Updated ER Model**

Create a full visual diagram of the final schema.

### **Functional Dependencies**

Use `normalization_report.md` — already includes this.

### **Normalization Analysis**

`normalization_report.md` demonstrates BCNF.

### **Constraints Analysis**

Explain why some logic belongs in the DB and some in the application.

#### **Constraints in the Database**

* **Foreign Keys** → Referential integrity
* **Primary Key / UNIQUE / NOT NULL** → Data integrity
* **Lot Number Trigger** → Ensures consistent lot-number format
* **Expiration Check Trigger** → Prevents consuming expired goods
* **Quantity Validation Trigger** → Prevents negative inventory
* **Evaluate_Health_Risk** → Critical business rule enforced transactionally

#### **Constraints in the Application**

* **FEFO logic** → Procedural, easiest in Python
* **Batch size multiple check** → UI validation (not a DB rule)

---

## **Task 4: Suggested Team Work Split**

### **Person 1 (DBA / You)**

* Lead author of Final Report
* Assist debugging Python (procedure calls, error handling)

### **Person 2 (App Lead — Manufacturer Role)**

* Implement Create Product Batch workflow (Section 1.3)

### **Person 3 (App Lead — Supplier / Viewer Roles)**

* Implement Main Shell (Login, Menus)
* Implement all “Simple” functions
  *(All stubs except `create_product_batch` and `run_manufacturer_reports`)*

### **Person 4 (Query & Report Lead)**

* Implement the 5 Required Queries (Section 2)
* Create final ER Diagram
* Prepare demo script

---
