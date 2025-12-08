# Database Data Dictionary - NEW Fridge System

**Date:** December 9, 2025
**Database:** PostgreSQL 16
**Total Tables:** 15
**Total Records:** ~71,095

**See Also:** [CASCADE_RULES.md](backend/docs/CASCADE_RULES.md) - Comprehensive foreign key cascade behavior documentation

---

## Table of Contents
1. [User Management](#1-user-management)
2. [Fridge & Inventory](#2-fridge--inventory)
3. [Recipes](#3-recipes)
4. [Procurement](#4-procurement)

---

## 1. User Management

### user
**Description:** User accounts with authentication and role management

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| user_id | UUID | NOT NULL | uuid_generate_v4() | PK | Unique user identifier |
| user_name | VARCHAR(20) | NOT NULL | - | UNIQUE | Login username |
| password | VARCHAR(60) | NOT NULL | - | - | Bcrypt hashed password |
| email | VARCHAR(50) | NOT NULL | - | UNIQUE | User email address |
| status | VARCHAR(10) | NOT NULL | - | CHECK: 'Active', 'Disabled' | Account status |
| role | user_role_enum | NOT NULL | 'User' | ENUM: 'Admin', 'User' | User role |

**Indexes:**
- `user_pkey` (PRIMARY KEY) on user_id
- `idx_user_role` (INDEX) on role
- `user_user_name_key` (UNIQUE) on user_name
- `user_email_key` (UNIQUE) on email

**Referenced By:**
- fridge_access.user_id
- meal_plan.user_id
- recipe.owner_id
- recipe_review.user_id
- shopping_list_item.user_id
- store_order.user_id

---

## 2. Fridge & Inventory

### fridge
**Description:** Shared fridge containers for storing ingredients

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| fridge_id | UUID | NOT NULL | uuid_generate_v4() | PK | Unique fridge identifier |
| fridge_name | VARCHAR(50) | NOT NULL | - | - | Display name |
| description | VARCHAR(200) | NULL | - | - | Optional description |

**Indexes:**
- `fridge_pkey` (PRIMARY KEY) on fridge_id

**Referenced By:**
- fridge_access.fridge_id
- fridge_item.fridge_id
- meal_plan.fridge_id
- store_order.fridge_id

---

### fridge_access
**Description:** User permissions for shared fridges (multi-tenancy)

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| user_id | UUID | NOT NULL | - | PK, FK → user.user_id | User with access |
| fridge_id | UUID | NOT NULL | - | PK, FK → fridge.fridge_id | Accessible fridge |
| access_role | VARCHAR(10) | NOT NULL | - | CHECK: 'Owner', 'Member' | Permission level |

**Composite Primary Key:** (user_id, fridge_id)

**Foreign Keys:**
- user_id → user.user_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- fridge_id → fridge.fridge_id (ON UPDATE CASCADE, ON DELETE CASCADE)

**Business Rules:**
- **Owner**: Can add/remove members, delete fridge
- **Member**: Can add/remove items

---

### ingredient
**Description:** Master catalog of all ingredients with standardized units

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| ingredient_id | BIGINT | NOT NULL | IDENTITY | PK | Unique ingredient identifier |
| name | VARCHAR(50) | NOT NULL | - | UNIQUE | Ingredient name |
| standard_unit | VARCHAR(10) | NOT NULL | - | CHECK: 'g', 'ml', 'pcs' | Unit of measurement |
| shelf_life_days | INTEGER | NOT NULL | - | CHECK: > 0 | Days until expiration |

**Indexes:**
- `ingredient_pkey` (PRIMARY KEY) on ingredient_id
- `ingredient_name_key` (UNIQUE) on name

**Referenced By:**
- external_product.ingredient_id
- fridge_item.ingredient_id
- recipe_requirement.ingredient_id
- shopping_list_item.ingredient_id

**Standard Units:**
- **g** - grams (weight)
- **ml** - milliliters (volume)
- **pcs** - pieces (count)

---

### fridge_item
**Description:** Inventory items in fridges with FIFO tracking

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| fridge_item_id | BIGINT | NOT NULL | IDENTITY | PK | Unique item identifier |
| fridge_id | UUID | NOT NULL | - | FK → fridge.fridge_id | Containing fridge |
| ingredient_id | BIGINT | NOT NULL | - | FK → ingredient.ingredient_id | Type of ingredient |
| quantity | NUMERIC(10,2) | NOT NULL | - | CHECK: >= 0 | Amount in standard_unit |
| entry_date | DATE | NOT NULL | - | - | When added to fridge |
| expiry_date | DATE | NOT NULL | - | - | Calculated expiration date |

**Indexes:**
- `fridge_item_pkey` (PRIMARY KEY) on fridge_item_id

**Foreign Keys:**
- fridge_id → fridge.fridge_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- ingredient_id → ingredient.ingredient_id (ON UPDATE CASCADE, ON DELETE RESTRICT)

**Business Logic:**
- expiry_date = entry_date + ingredient.shelf_life_days
- FIFO consumption: Sort by expiry_date ASC

---

## 3. Recipes

### recipe
**Description:** User-created recipes with approval workflow

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| recipe_id | BIGINT | NOT NULL | IDENTITY | PK | Unique recipe identifier |
| owner_id | UUID | NOT NULL | - | FK → user.user_id | Recipe creator |
| recipe_name | VARCHAR(100) | NOT NULL | - | - | Display name |
| cooking_time | INTEGER | NULL | - | CHECK: > 0 | Minutes to cook |
| status | VARCHAR(10) | NOT NULL | - | CHECK: 'Pending', 'Published', 'Approved' | Approval status |
| description | VARCHAR(500) | NULL | - | - | Recipe description |
| created_at | TIMESTAMP | NOT NULL | now() AT TIME ZONE 'utc' | - | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | now() AT TIME ZONE 'utc' | - | Last update timestamp |

**Indexes:**
- `recipe_pkey` (PRIMARY KEY) on recipe_id

**Foreign Keys:**
- owner_id → user.user_id (ON UPDATE CASCADE, ON DELETE RESTRICT)

**Referenced By:**
- meal_plan.recipe_id
- recipe_requirement.recipe_id
- recipe_review.recipe_id
- recipe_step.recipe_id

---

### recipe_requirement
**Description:** Ingredients needed for recipes

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| recipe_id | BIGINT | NOT NULL | - | PK, FK → recipe.recipe_id | Parent recipe |
| ingredient_id | BIGINT | NOT NULL | - | PK, FK → ingredient.ingredient_id | Required ingredient |
| quantity_needed | NUMERIC(10,2) | NOT NULL | - | CHECK: > 0 | Amount in standard_unit |

**Composite Primary Key:** (recipe_id, ingredient_id)

**Foreign Keys:**
- recipe_id → recipe.recipe_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- ingredient_id → ingredient.ingredient_id (ON UPDATE CASCADE, ON DELETE RESTRICT)

---

### recipe_step
**Description:** Ordered cooking instructions for recipes

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| recipe_id | BIGINT | NOT NULL | - | PK, FK → recipe.recipe_id | Parent recipe |
| step_number | INTEGER | NOT NULL | - | PK, CHECK: > 0 | Step order |
| description | VARCHAR(1000) | NOT NULL | - | - | Instruction text |

**Composite Primary Key:** (recipe_id, step_number)

**Foreign Keys:**
- recipe_id → recipe.recipe_id (ON UPDATE CASCADE, ON DELETE CASCADE)

---

### recipe_review
**Description:** User ratings and reviews for recipes

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| user_id | UUID | NOT NULL | - | PK, FK → user.user_id | Reviewer |
| recipe_id | BIGINT | NOT NULL | - | PK, FK → recipe.recipe_id | Reviewed recipe |
| rating | INTEGER | NOT NULL | - | CHECK: 1-5 | Star rating |
| comment | VARCHAR(500) | NULL | - | - | Optional review text |
| review_date | TIMESTAMP | NOT NULL | - | - | Review timestamp |

**Composite Primary Key:** (user_id, recipe_id)

**Foreign Keys:**
- user_id → user.user_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- recipe_id → recipe.recipe_id (ON UPDATE CASCADE, ON DELETE CASCADE)

---

### meal_plan
**Description:** Planned meals tied to specific fridges

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| plan_id | BIGINT | NOT NULL | IDENTITY | PK | Unique plan identifier |
| user_id | UUID | NOT NULL | - | FK → user.user_id | User who created plan |
| recipe_id | BIGINT | NOT NULL | - | FK → recipe.recipe_id | Planned recipe |
| planned_date | TIMESTAMP | NOT NULL | - | - | When to cook |
| status | VARCHAR(30) | NOT NULL | 'Planned' | - | Plan status |
| fridge_id | UUID | NOT NULL | - | FK → fridge.fridge_id | Associated fridge |

**Indexes:**
- `meal_plan_pkey` (PRIMARY KEY) on plan_id

**Foreign Keys:**
- user_id → user.user_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- recipe_id → recipe.recipe_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- fridge_id → fridge.fridge_id (ON UPDATE CASCADE, ON DELETE CASCADE)

**Business Logic:**
- All users with access to fridge can see meal plans
- Meal plans deleted when fridge is deleted

---

## 4. Procurement

### partner
**Description:** Suppliers and stores for product procurement

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| partner_id | BIGINT | NOT NULL | IDENTITY | PK | Unique partner identifier |
| partner_name | VARCHAR(50) | NOT NULL | - | - | Supplier name |
| contract_date | DATE | NOT NULL | - | - | Partnership start date |
| avg_shipping_days | INTEGER | NOT NULL | - | CHECK: > 0 | Average delivery time |
| credit_score | INTEGER | NOT NULL | - | CHECK: 0-100 | Reliability score |

**Indexes:**
- `partner_pkey` (PRIMARY KEY) on partner_id

**Referenced By:**
- external_product.partner_id
- store_order.partner_id

---

### external_product
**Description:** Products sold by partners with unit conversion

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| partner_id | BIGINT | NOT NULL | - | PK (composite), FK → partner.partner_id | Selling partner |
| external_sku | VARCHAR(50) | NOT NULL | - | PK (composite) | Product SKU |
| ingredient_id | BIGINT | NOT NULL | - | FK → ingredient.ingredient_id | Base ingredient |
| product_name | VARCHAR(100) | NOT NULL | - | - | Display name |
| current_price | NUMERIC(10,2) | NOT NULL | - | CHECK: > 0 | Current selling price |
| selling_unit | VARCHAR(20) | NOT NULL | - | - | Package description |
| unit_quantity | NUMERIC(10,2) | NOT NULL | 1.00 | CHECK: > 0 | Conversion to standard_unit |

**Composite Primary Key:** (partner_id, external_sku)

**Indexes:**
- `external_product_pkey` (PRIMARY KEY) on (partner_id, external_sku)

**Foreign Keys:**
- partner_id → partner.partner_id (ON UPDATE CASCADE, ON DELETE RESTRICT)
- ingredient_id → ingredient.ingredient_id (ON UPDATE CASCADE, ON DELETE RESTRICT)

**Referenced By:**
- order_item (composite FK on partner_id, external_sku)

**Design Rationale:**
- Composite primary key allows multiple partners to use the same SKU names independently
- Each partner maintains their own SKU namespace

**Unit Conversion Example:**
- Product: "Milk 1L Bottle"
- selling_unit: "1L Bottle"
- unit_quantity: 1000 (means 1 bottle = 1000ml)
- ingredient.standard_unit: "ml"

**Calculation:**
```
bottles_needed = CEIL(quantity_needed / unit_quantity)
Example: Need 2000ml → CEIL(2000 / 1000) = 2 bottles
```

---

### shopping_list_item
**Description:** User shopping cart with optional deadlines

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| user_id | UUID | NOT NULL | - | PK, FK → user.user_id | Shopping user |
| ingredient_id | BIGINT | NOT NULL | - | PK, FK → ingredient.ingredient_id | Desired ingredient |
| quantity_to_buy | NUMERIC(10,2) | NOT NULL | - | CHECK: > 0 | Amount in standard_unit |
| added_date | DATE | NOT NULL | - | - | When added to cart |
| needed_by | DATE | NULL | - | - | Optional deadline |

**Composite Primary Key:** (user_id, ingredient_id)

**Foreign Keys:**
- user_id → user.user_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- ingredient_id → ingredient.ingredient_id (ON UPDATE CASCADE, ON DELETE RESTRICT)

**Business Logic:**
- Used to filter products by expected_arrival < needed_by
- Helps prioritize urgent shopping items

---

### store_order
**Description:** Purchase orders placed with partners for specific fridges (financial records)

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| order_id | BIGINT | NOT NULL | IDENTITY | PK | Unique order identifier |
| user_id | UUID | NOT NULL | - | FK → user.user_id | Ordering user |
| partner_id | BIGINT | NOT NULL | - | FK → partner.partner_id | Supplier |
| fridge_id | UUID | **NULL** | - | FK → fridge.fridge_id | Destination fridge (nullable) |
| order_date | TIMESTAMP | NOT NULL | - | - | When order was placed |
| expected_arrival | DATE | NULL | - | - | Calculated delivery date |
| total_price | NUMERIC(10,2) | NOT NULL | - | CHECK: >= 0 | Order total |
| order_status | VARCHAR(15) | NOT NULL | - | CHECK: 'Pending', 'Paid', 'Shipped', 'Delivered', 'Cancelled' | Order state |

**Indexes:**
- `store_order_pkey` (PRIMARY KEY) on order_id

**Foreign Keys:**
- user_id → user.user_id (ON UPDATE CASCADE, ON DELETE RESTRICT)
- partner_id → partner.partner_id (ON UPDATE CASCADE, ON DELETE RESTRICT)
- fridge_id → fridge.fridge_id (ON UPDATE CASCADE, **ON DELETE SET NULL**)

**Referenced By:**
- order_item.order_id

**Business Logic:**
- expected_arrival = order_date + partner.avg_shipping_days
- Shopping cart items grouped by partner_id create split orders
- **Financial Record Preservation**: Orders are immutable audit records
  - User/partner deletion BLOCKED if orders exist (RESTRICT)
  - Fridge deletion ALLOWED: fridge_id set to NULL, order preserved
  - This allows normal fridge lifecycle while maintaining complete order history

---

### order_item
**Description:** Line items in purchase orders with price snapshots

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| order_id | BIGINT | NOT NULL | - | PK, FK → store_order.order_id | Parent order |
| external_sku | VARCHAR(50) | NOT NULL | - | PK, Composite FK | Ordered product SKU |
| partner_id | BIGINT | NOT NULL | - | Composite FK | Partner identifier |
| quantity | INTEGER | NOT NULL | - | CHECK: > 0 | Number of units |
| deal_price | NUMERIC(10,2) | NOT NULL | - | - | Price snapshot |

**Composite Primary Key:** (order_id, external_sku)

**Foreign Keys:**
- order_id → store_order.order_id (ON UPDATE CASCADE, ON DELETE CASCADE)
- **(partner_id, external_sku)** → external_product (ON UPDATE CASCADE, ON DELETE RESTRICT)

**Business Logic:**
- deal_price is a snapshot of current_price at order time
- Never join to external_product.current_price for historical analysis
- Composite FK ensures product belongs to the partner specified in parent order
- Partner_id stored redundantly for composite FK and query optimization

---

## Foreign Key Summary

### Cascade Rules

**ON DELETE CASCADE** (child deleted when parent deleted):
- fridge_access → user, fridge
- fridge_item → fridge
- meal_plan → user, recipe, fridge
- order_item → store_order
- recipe_requirement → recipe
- recipe_review → user, recipe
- recipe_step → recipe
- shopping_list_item → user

**ON DELETE RESTRICT** (prevent parent deletion if child exists):
- external_product → partner, ingredient
- fridge_item → ingredient
- order_item → external_product (composite FK)
- recipe → user
- recipe_requirement → ingredient
- shopping_list_item → ingredient
- store_order → user, partner

**ON DELETE SET NULL** (set FK to NULL when parent deleted):
- store_order.fridge_id → fridge ⚠️ **SPECIAL CASE**
  - Only FK in entire schema using SET NULL
  - Preserves financial records when fridge deleted
  - See [CASCADE_RULES.md](backend/docs/CASCADE_RULES.md) for details

**ON UPDATE CASCADE** (all foreign keys)

---

## Enums and Check Constraints

### user.role (ENUM)
- `Admin` - System administrator
- `User` - Regular user (default)

### user.status (CHECK)
- `Active` - Account enabled
- `Disabled` - Account suspended

### fridge_access.access_role (CHECK)
- `Owner` - Full control (add/remove members, delete fridge)
- `Member` - Item management only

### ingredient.standard_unit (CHECK)
- `g` - grams (weight)
- `ml` - milliliters (volume)
- `pcs` - pieces (count)

### recipe.status (CHECK)
- `Pending` - Awaiting approval
- `Published` - User published
- `Approved` - Admin approved

### store_order.order_status (CHECK)
- `Pending` - Order created
- `Paid` - Payment confirmed
- `Shipped` - In transit
- `Delivered` - Received
- `Cancelled` - Order cancelled

---

## Indexes

**Performance Optimized:**
- All primary keys (automatic B-tree indexes)
- All foreign keys (automatic indexes)
- `idx_user_role` on user.role (role filtering)
- Unique constraints (automatic unique indexes):
  - user.user_name
  - user.email
  - ingredient.name

---

## Database Statistics

| Table | Record Count | Purpose |
|-------|--------------|---------|
| user | 500 | 3 admins, 497 regular users |
| ingredient | 41 | Master ingredient catalog |
| fridge | 200 | Shared fridges |
| fridge_access | 398 | Permission records |
| fridge_item | 50,000 | Inventory with FIFO |
| recipe | 4 | User recipes |
| recipe_requirement | 16 | Recipe ingredients |
| recipe_step | 18 | Cooking instructions |
| partner | 10 | Suppliers/stores |
| external_product | 216 | Products for sale |
| shopping_list_item | 0 | Shopping carts (empty) |
| meal_plan | 0 | Planned meals (empty) |
| store_order | 5,625 | Purchase orders |
| order_item | 14,067 | Order line items |
| **TOTAL** | **~71,095** | **All records** |

---

## Key Business Rules

1. **Multi-Tenancy**: Fridges support multiple users via fridge_access
2. **FIFO Inventory**: Oldest items (by expiry_date) consumed first
3. **Unit Conversion**: Buying by package, storing by standard unit
4. **Split Orders**: Shopping cart grouped by partner_id
5. **Price History**: deal_price preserves order-time pricing
6. **Fridge-Centric**: Orders and meal plans tied to fridges
7. **Access Control**: Owner vs Member permissions

---

**Last Updated:** December 8, 2025
**Schema Version:** 2.0 (with fridge-centric design)
**Backup:** `db_backup_20251208_224911.sql.gz` (916KB)
