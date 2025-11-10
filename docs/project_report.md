# CSC540 Project 1: Inventory Management System
## Project Report

### Team Members
[To be filled]

---

## 1. Functional Dependencies

The following functional dependencies influenced the database design:

### 1.1 User and Role Dependencies
- `user_id → username, password, role, name, contact_info`
  - Each user has a unique ID that determines all user attributes
- `user_id → role` (partial dependency)
  - This led to separate MANUFACTURERS and SUPPLIERS tables to avoid NULL values
- `user_id → manufacturer_id` (for Manufacturer role)
- `user_id → supplier_id` (for Supplier role)

### 1.2 Product Dependencies
- `product_id → manufacturer_id, category_id, product_name, standard_batch_size, created_date`
- `(product_name, manufacturer_id) → product_id`
  - Product names are unique per manufacturer (enforced by unique constraint)
- `manufacturer_id → manufacturer_name`
- `category_id → category_name`

### 1.3 Ingredient Dependencies
- `ingredient_id → ingredient_name, ingredient_type, unit_of_measure, description`
- `(parent_ingredient_id, child_ingredient_id) → quantity_required`
  - Composite key for ingredient compositions
- `ingredient_type = 'Compound' → exists INGREDIENT_COMPOSITIONS entry`
  - This is a business rule enforced in application code

### 1.4 Batch Dependencies
- `ingredient_batch_id → ingredient_id, supplier_id, lot_number, quantity_on_hand, cost_per_unit, expiration_date, received_date`
- `lot_number → ingredient_batch_id`
  - Lot numbers are unique (enforced by unique constraint)
- `(ingredient_id, supplier_id, batch_counter) → lot_number`
  - Lot number format: `<ingredientId>-<supplierId>-B<batchId>`
- `product_batch_id → product_id, plan_id, batch_number, quantity_produced, total_cost, cost_per_unit, production_date, expiration_date`
- `batch_number → product_batch_id`
  - Batch numbers are unique

### 1.5 Recipe Dependencies
- `plan_id → product_id, version_number, created_date, is_active`
- `(product_id, version_number) → plan_id`
  - Unique recipe plan version per product
- `(plan_id, ingredient_id) → quantity_required`
  - Composite key for recipe ingredients

### 1.6 Supplier Dependencies
- `(supplier_id, ingredient_id) → is_active`
  - Which ingredients each supplier can provide
- `formulation_id → supplier_id, ingredient_id, name`
- `version_id → formulation_id, pack_size, unit_price, effective_from, effective_to, is_active`
- `(formulation_id, effective_from) → version_id`
  - Versioning with effective dates

### 1.7 Consumption Dependencies
- `(product_batch_id, ingredient_batch_id) → quantity_used`
  - Composite key tracking which ingredient batches were used in which product batches

### 1.8 Decomposition Decisions
The following decompositions were made to achieve higher normal forms:

1. **USERS → MANUFACTURERS/SUPPLIERS**: 
   - Decomposed to avoid NULL values and ensure one role per user
   - Functional dependency: `user_id → role` determines which table to use

2. **No further decomposition needed**: 
   - All tables are in BCNF or 3NF as shown in the normalization section

---

## 2. Normalization Analysis

### 2.1 Normalization Status by Table

| Table Name | Normal Form | Justification |
|-----------|------------|---------------|
| USERS | BCNF | All attributes fully functionally dependent on primary key `user_id` |
| MANUFACTURERS | BCNF | `manufacturer_id` is primary key, `user_id` is unique foreign key |
| SUPPLIERS | BCNF | `supplier_id` is primary key, `user_id` is unique foreign key |
| CATEGORIES | BCNF | Simple table with `category_id` as primary key |
| PRODUCTS | BCNF | All attributes depend on `product_id`; unique constraint on `(product_name, manufacturer_id)` is a business rule |
| INGREDIENTS | BCNF | All attributes depend on `ingredient_id` |
| INGREDIENT_COMPOSITIONS | BCNF | Composite primary key `(parent_ingredient_id, child_ingredient_id)`; `quantity_required` depends on both |
| SUPPLIER_INGREDIENTS | BCNF | Composite primary key `(supplier_id, ingredient_id)`; `is_active` depends on both |
| FORMULATIONS | BCNF | All attributes depend on `formulation_id` |
| FORMULATION_VERSIONS | BCNF | All attributes depend on `version_id` |
| INGREDIENT_BATCHES | BCNF | All attributes depend on `ingredient_batch_id`; `lot_number` is unique |
| RECIPE_PLANS | BCNF | All attributes depend on `plan_id`; unique constraint on `(product_id, version_number)` is a business rule |
| RECIPE_INGREDIENTS | BCNF | Composite primary key `(plan_id, ingredient_id)`; `quantity_required` depends on both |
| PRODUCT_BATCHES | BCNF | All attributes depend on `product_batch_id`; `batch_number` is unique |
| BATCH_CONSUMPTION | BCNF | Composite primary key `(product_batch_id, ingredient_batch_id)`; `quantity_used` depends on both |
| DO_NOT_COMBINE | BCNF | Composite primary key with unique constraints ensuring bidirectional uniqueness |

### 2.2 Normalization Justification

**All tables are in BCNF (Boyce-Codd Normal Form)** because:
1. Every determinant is a candidate key
2. No partial dependencies exist
3. No transitive dependencies exist
4. All functional dependencies are fully satisfied by primary or unique keys

**No tables are below 3NF** - all tables meet at least 3NF requirements:
- No partial dependencies (2NF satisfied)
- No transitive dependencies (3NF satisfied)
- All determinants are candidate keys (BCNF satisfied)

### 2.3 Design Decisions

1. **Separate MANUFACTURERS and SUPPLIERS tables**: 
   - Prevents NULL values that would occur if using a single table with optional foreign keys
   - Ensures referential integrity and simplifies queries

2. **Composite keys for many-to-many relationships**:
   - INGREDIENT_COMPOSITIONS, SUPPLIER_INGREDIENTS, RECIPE_INGREDIENTS, BATCH_CONSUMPTION
   - These represent true many-to-many relationships with attributes

3. **Versioning in RECIPE_PLANS and FORMULATION_VERSIONS**:
   - Maintains history while allowing active version tracking
   - `is_active` flag simplifies queries for current versions

---

## 3. Constraints

### 3.1 Constraints Implemented in Database

#### 3.1.1 Primary Key Constraints
- All tables have primary keys ensuring entity integrity
- Composite primary keys used where appropriate

#### 3.1.2 Foreign Key Constraints
- All foreign keys have referential integrity constraints
- ON DELETE CASCADE used for dependent entities (e.g., products when manufacturer deleted)
- ON DELETE RESTRICT used for critical entities (e.g., ingredients used in batches)

#### 3.1.3 Unique Constraints
- `USERS.username` - unique usernames
- `USERS.user_id` in MANUFACTURERS and SUPPLIERS - one-to-one relationship
- `PRODUCTS(product_name, manufacturer_id)` - unique product names per manufacturer
- `INGREDIENT_BATCHES.lot_number` - unique lot numbers
- `PRODUCT_BATCHES.batch_number` - unique batch numbers
- `RECIPE_PLANS(product_id, version_number)` - unique versions per product
- `DO_NOT_COMBINE` - bidirectional uniqueness for ingredient pairs

#### 3.1.4 Check Constraints
- `PRODUCTS.standard_batch_size > 0` - positive batch sizes
- `INGREDIENT_COMPOSITIONS.quantity_required > 0` - positive quantities
- `INGREDIENT_BATCHES.quantity_on_hand >= 0` - non-negative inventory
- `INGREDIENT_BATCHES.cost_per_unit >= 0` - non-negative costs
- `PRODUCT_BATCHES.quantity_produced > 0` - positive production quantities
- `PRODUCT_BATCHES.total_cost >= 0` and `cost_per_unit >= 0` - non-negative costs
- `FORMULATION_VERSIONS.pack_size > 0` and `unit_price >= 0` - valid pricing
- `FORMULATION_VERSIONS.effective_to >= effective_from` - valid date ranges
- `INGREDIENT_COMPOSITIONS.parent_ingredient_id != child_ingredient_id` - no self-inclusion
- `DO_NOT_COMBINE.ingredient1_id != ingredient2_id` - no self-conflict

#### 3.1.5 ENUM Constraints
- `USERS.role` - ENUM('Manufacturer', 'Supplier', 'Viewer')
- `INGREDIENTS.ingredient_type` - ENUM('Atomic', 'Compound')

#### 3.1.6 Trigger-Based Constraints

**Trigger 1: `trg_compute_ingredient_lot_number`**
- Automatically computes lot number format: `<ingredientId>-<supplierId>-B<batchId>`
- Validates lot number format matches pattern
- Enforces uniqueness through auto-incrementing batch counter

**Trigger 2: `trg_prevent_expired_consumption`**
- Prevents consumption of expired ingredient batches
- Checks expiration date before allowing BATCH_CONSUMPTION insert

**Trigger 3: `trg_maintain_onhand_consumption`**
- Automatically decrements `quantity_on_hand` when batches are consumed
- Validates sufficient quantity available

**Trigger 4: `trg_validate_ingredient_expiration`**
- Enforces 90-day rule: expiration date must be at least 90 days from received date
- Rejects batches that don't meet this requirement

**Trigger 5: `trg_validate_product_batch_number`**
- Validates product batch number format: `<productId>-<manufacturerId>-B<batchId>`
- Ensures format matches business rules

### 3.2 Constraints Implemented in Application Code

#### 3.2.1 Business Logic Constraints

**1. One-Level Composition Limit**
- **Constraint**: Compound ingredients can only have one level of children (no grandchildren)
- **Implementation**: Application code validates that when adding a material to a compound ingredient, the material itself must be atomic (not compound)
- **Reason**: This is a complex recursive constraint that would require recursive CTEs or stored procedures to validate in the database. Application-level validation is more maintainable and provides better error messages.

**2. FEFO (First Expired First Out) Selection**
- **Constraint**: When multiple batches exist for the same ingredient, prefer the closest-to-expiration lot first
- **Implementation**: Stored procedure `sp_record_production_batch` includes FEFO logic, but full implementation with batch splitting would require complex application logic
- **Reason**: The requirement states "Splitting is NOT allowed", so the procedure selects the earliest batch that has sufficient quantity. If multiple batches are needed, this requires iterative selection logic best handled in application code.

**3. Recipe Plan Versioning**
- **Constraint**: Updating a recipe plan creates a new version; previous versions remain for history
- **Implementation**: Application code creates new RECIPE_PLANS entry and deactivates old ones
- **Reason**: This is a business process that involves multiple steps (insert new, update old) that should be atomic. While this could be done in a stored procedure, the application provides better user feedback during the process.

**4. Access Control**
- **Constraint**: Manufacturers can only act on products they own; suppliers can only create batches for ingredients they supply
- **Implementation**: Application code checks ownership/supplier relationships before allowing operations
- **Reason**: While this could be implemented using database views with row-level security, the project requirements specify "No support for database level privileges is required. Just regular application level role management using passwords."

**5. Standard Batch Size Multiple Validation**
- **Constraint**: Production quantity must be an integer multiple of the product's standard batch size
- **Implementation**: Stored procedure validates this, but application also validates before calling procedure
- **Reason**: Provides immediate user feedback before database round-trip

**6. Do-Not-Combine Conflict Detection**
- **Constraint**: Warn when recipe plans or product batches contain incompatible ingredient pairs
- **Implementation**: Stored procedure `sp_evaluate_health_risk` checks for conflicts, but application code provides user-friendly warnings
- **Reason**: The procedure detects conflicts, but the decision to block or warn is a business process best handled in application code

#### 3.2.2 Data Validation Constraints

**1. Ingredient Type Validation**
- **Constraint**: Compound ingredients must have at least one material; atomic ingredients cannot have materials
- **Implementation**: Application code validates this when creating/updating ingredients
- **Reason**: This is a conditional constraint (IF type='Compound' THEN must have materials) that is easier to validate in application code with clear error messages

**2. Formulation Version Overlap Prevention**
- **Constraint**: Formulation versions should not have overlapping effective periods for the same formulation
- **Implementation**: Application code checks for overlaps before inserting new versions
- **Reason**: While this could be implemented using triggers, the validation logic is complex (checking date ranges) and application code provides better error handling

**3. Active Formulation Selection**
- **Constraint**: Only one formulation version should be active at a time for a given formulation
- **Implementation**: Application code deactivates old versions when activating a new one
- **Reason**: This is a business process that involves multiple updates; application code ensures atomicity and provides user feedback

### 3.3 Constraints That Could Not Be Implemented

#### 3.3.1 Complex Recursive Constraints

**1. No Cycles in Ingredient Composition**
- **Constraint**: Ingredient compositions should not form cycles (A contains B, B contains A)
- **Status**: Partially implemented (self-inclusion prevented by CHECK constraint)
- **Reason**: Full cycle detection would require recursive queries or graph traversal algorithms that are computationally expensive in database triggers. Application code can validate this more efficiently.

**2. Maximum Composition Depth**
- **Constraint**: Ingredients can only have one level of nesting (no grandchildren)
- **Status**: Enforced in application code
- **Reason**: Validating that a material's materials don't have materials requires recursive checking that is better handled in application code

#### 3.3.2 Temporal Constraints

**1. Non-Overlapping Formulation Versions**
- **Constraint**: Formulation versions for the same formulation should not have overlapping effective date ranges
- **Status**: Enforced in application code
- **Reason**: While this could be implemented using triggers, the validation requires checking all existing versions, which is more efficiently done in application code with better error messages

**2. Future-Dated Batches**
- **Constraint**: Production dates and received dates should not be in the future
- **Status**: Not enforced (could be added as CHECK constraint)
- **Reason**: This was considered but not implemented to allow for planning purposes. Could easily be added if needed.

#### 3.3.3 Aggregate Constraints

**1. Sufficient Inventory for Production**
- **Constraint**: Total available inventory across all batches must meet production requirements
- **Status**: Enforced in stored procedure `sp_record_production_batch`
- **Reason**: This requires aggregating across multiple batches and comparing to requirements. The stored procedure handles this, but complex scenarios (splitting across batches) are better handled in application code.

**2. Cost Calculation Accuracy**
- **Constraint**: Product batch costs should equal sum of consumed ingredient batch costs
- **Status**: Enforced in stored procedure
- **Reason**: The procedure calculates costs atomically, ensuring accuracy. Application code could validate this, but the procedure ensures it's always correct.

### 3.4 Summary of Constraint Implementation Strategy

| Constraint Type | Database | Application | Reason |
|----------------|----------|-------------|---------|
| Primary/Foreign Keys | ✓ | | Standard referential integrity |
| Unique Constraints | ✓ | | Data uniqueness requirements |
| Check Constraints | ✓ | | Simple value validations |
| ENUM Constraints | ✓ | | Limited value sets |
| Format Validation | ✓ (Triggers) | | Lot number formats |
| Expiration Rules | ✓ (Triggers) | | 90-day rule, expired consumption |
| Inventory Updates | ✓ (Triggers) | | Automatic on-hand maintenance |
| Complex Business Logic | | ✓ | Multi-step processes, better UX |
| Recursive Validations | | ✓ | Performance, maintainability |
| Access Control | | ✓ | Project requirement |
| FEFO Logic | Partial (SP) | ✓ | Complex selection algorithms |

---

## 4. Design Improvements from Preliminary Design

### 4.1 Changes Made

1. **Added FORMULATIONS and FORMULATION_VERSIONS tables**:
   - Initially considered embedding formulation data in SUPPLIER_INGREDIENTS
   - Separated to support versioning and effective date management
   - Allows suppliers to maintain price history and version control

2. **Enhanced DO_NOT_COMBINE table**:
   - Added bidirectional uniqueness constraints
   - Added reason field for better traceability
   - Made it supplier-agnostic (general regulatory list) as per requirements

3. **Improved Batch Number Generation**:
   - Added triggers to automatically compute lot numbers
   - Validated format using regular expressions
   - Ensured uniqueness through auto-incrementing counters

4. **Added Comprehensive Views**:
   - `vw_active_formulations` - simplifies active formulation queries
   - `vw_flattened_product_bom` - handles nested ingredient flattening for labeling
   - `vw_health_risk_violations` - provides health risk reporting

5. **Enhanced Stored Procedures**:
   - `sp_record_production_batch` - atomic batch creation with cost calculation
   - `sp_trace_recall` - recall traceability with time windows
   - `sp_evaluate_health_risk` - conflict detection for do-not-combine rules

6. **Added Indexes for Performance**:
   - Indexes on expiration dates for FEFO queries
   - Indexes on lot numbers and batch numbers for lookups
   - Indexes on active flags for filtering

### 4.2 Rationale

These improvements were made to:
- Better support business requirements (versioning, traceability)
- Improve query performance (indexes, views)
- Ensure data integrity (triggers, constraints)
- Simplify application development (stored procedures, views)
- Meet all project requirements (recall traceability, health risk evaluation)

---

## 5. Conclusion

The database design successfully implements all required functionality while maintaining:
- **Data Integrity**: Through comprehensive constraints, triggers, and referential integrity
- **Normalization**: All tables are in BCNF, ensuring no redundancy
- **Performance**: Strategic use of indexes and views
- **Maintainability**: Clear separation of concerns between database and application logic
- **Extensibility**: Design supports future enhancements (additional roles, features)

The implementation balances database-enforced constraints (for data integrity) with application-level logic (for complex business rules and user experience), following best practices for database design.


