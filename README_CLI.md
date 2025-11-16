# Meal Manufacturer CLI System

A comprehensive command-line interface for managing meal manufacturing operations, supplier relationships, and product tracking.

## Setup

### Prerequisites
- Python 3.6+
- MySQL/MariaDB server
- mysql-connector-python package

### Installation

1. Install Python dependencies:
```bash
pip install mysql-connector-python
```

2. Set up the database:
```bash
# Create schema
python src/run_schema.py

# Insert sample data
python src/run_data.py

# Create procedures and triggers
python src/run_procedures_triggers.py
```

## Running the CLI

```bash
python src/cli_main.py
```

## Features

### Role-Based Access

The system supports three roles:

1. **Manufacturer** - Product management, recipe planning, batch production, inventory reports
2. **Supplier** - Ingredient management, formulations, lot creation
3. **Viewer** - Read-only access to browse products and view ingredient lists

### Manufacturer Functions

- **Define/Update Product**: Create and manage product types with categories and batch sizes
- **Define/Update Recipe Plans**: Create versioned BOMs (Bill of Materials) for products
- **Record Ingredient Receipt**: Record incoming ingredient batches (enforces 90-day expiration rule)
- **Create Product Batch**: Produce batches with lot consumption, cost calculation, and validation
- **Reports**:
  - On-hand inventory by item/lot
  - Nearly out of stock items
  - Almost expired ingredient lots
  - Batch cost summary
- **Recall/Traceability** (Grad): Trace affected product batches from ingredient or lot

### Supplier Functions

- **Manage Ingredients Supplied**: Maintain list of ingredients this supplier provides
- **Define/Update Ingredient**: Create atomic or compound ingredients with compositions
- **Maintain Do-Not-Combine List** (Grad): Define incompatible ingredient pairs
- **Maintain Formulations**: Create and version ingredient formulations with pricing
- **Create Ingredient Batch**: Record lot intake with automatic lot number generation

### Viewer Functions

- **Browse Products**: View all products organized by manufacturer and category
- **Generate Ingredient List**: Get flattened ingredient lists for products (one-level expansion)
- **Compare Products** (Grad): Check for incompatibilities between two products

### Queries

Five pre-defined queries are available:

1. List ingredients and lot numbers for last batch of Steak Dinner (100) by MFG001
2. Suppliers and total spending for manufacturer MFG002
3. Unit cost for product batch 100-MFG001-B0901
4. Conflicting ingredients for product batch 100-MFG001-B0901
5. Manufacturers NOT supplied by James Miller (21)

## Database Features

### Triggers

- **Lot Number Validation**: Enforces format `ingredientId-supplierId-batchId` and uniqueness
- **Expired Consumption Prevention**: Blocks consumption of expired ingredient lots
- **On-Hand Maintenance**: Validates inventory quantities

### Stored Procedures

- **RecordProductionBatch**: Atomically creates batch, consumes lots, calculates costs
- **TraceRecall**: Finds affected product batches from ingredient ID or lot number
- **EvaluateHealthRisk**: Checks for do-not-combine conflicts in batches

### Views

- **v_active_supplier_formulations**: Current active supplier formulations
- **v_flattened_product_bom**: Flattened BOM for product labeling
- **v_health_risk_violations**: Health risk violations in last 30 days

## Sample Users

The sample data includes:

- **Manufacturers**:
  - MFG001 (johnsmith / password123) - John Smith Manufacturing
  - MFG002 (alicelee / password123) - Alice Lee Foods

- **Suppliers**:
  - SUP020 (janedoe / password123) - Jane Doe
  - SUP021 (jamesmiller / password123) - James Miller

- **Viewer**:
  - VIEW001 (bobjohnson / password123) - Bob Johnson

## Business Rules

1. **90-Day Rule**: Ingredient expiration must be at least 90 days from receipt date
2. **Batch Size Multiple**: Product batch quantities must be multiples of standard batch size
3. **Lot Number Format**: `ingredientId-supplierId-batchId`
4. **No Expired Consumption**: Cannot consume expired ingredient lots
5. **Access Control**: Manufacturers can only manage their own products; suppliers can only create batches for ingredients they supply

## Notes

- All dates should be in `YYYY-MM-DD` format
- Quantities are in ounces (oz)
- Costs are in dollars
- The system uses transactions to ensure data consistency
- Foreign key constraints are enforced (except during initial data load)



