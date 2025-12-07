# PostgreSQL Database Schema - NEW Fridge System

## Overview
Total Tables: **16**
- User & Authentication: 2 tables
- Fridge Management: 3 tables
- Inventory: 2 tables
- Recipe System: 5 tables
- Procurement: 4 tables

---

## 📊 Complete Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER & AUTHENTICATION                       │
└─────────────────────────────────────────────────────────────────┘
    user (UUID)
      ├── user_role (user_id, role_name) [M:M]
      ├── fridge_access (user_id, fridge_id, role) [M:M]
      ├── shopping_list_item (user_id, ingredient_id) [M:M]
      ├── store_order (user_id → order_id)
      ├── recipe (owner_id → recipe_id)
      ├── recipe_review (user_id, recipe_id)
      └── meal_plan (user_id, recipe_id, planned_date)

┌─────────────────────────────────────────────────────────────────┐
│                      FRIDGE MANAGEMENT                          │
└─────────────────────────────────────────────────────────────────┘
    fridge (UUID)
      ├── fridge_access (fridge_id, user_id, role) [shared access]
      └── fridge_item (fridge_id, ingredient_id, quantity, expiry_date)

┌─────────────────────────────────────────────────────────────────┐
│                         INVENTORY                               │
└─────────────────────────────────────────────────────────────────┘
    ingredient (ingredient_id)
      ├── fridge_item (ingredient_id → quantity in fridges)
      ├── recipe_requirement (ingredient_id → needed in recipes)
      ├── external_product (ingredient_id → available from partners)
      └── shopping_list_item (ingredient_id → user wants to buy)

┌─────────────────────────────────────────────────────────────────┐
│                        RECIPE SYSTEM                            │
└─────────────────────────────────────────────────────────────────┘
    recipe (recipe_id)
      ├── recipe_requirement (recipe_id, ingredient_id, quantity_needed)
      ├── recipe_step (recipe_id, step_number, description)
      ├── recipe_review (recipe_id, user_id, rating, comment)
      └── meal_plan (recipe_id, user_id, planned_date, status)

┌─────────────────────────────────────────────────────────────────┐
│                       PROCUREMENT                               │
└─────────────────────────────────────────────────────────────────┘
    partner (partner_id)
      ├── external_product (partner_id, ingredient_id, price, sku)
      └── store_order (partner_id → orders from this partner)
            └── order_item (order_id, external_sku, quantity, deal_price)
```

---

## 1. USER & AUTHENTICATION TABLES

### `user` (Primary user accounts)
```sql
CREATE TABLE "user" (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',  -- 'Active' or 'Disabled'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- PRIMARY KEY on `user_id`
- UNIQUE on `user_name`
- UNIQUE on `email`

**Relationships:**
- → `user_role` (1:M) - User has multiple roles
- → `fridge_access` (1:M) - User can access multiple fridges
- → `shopping_list_item` (1:M) - User's shopping list
- → `store_order` (1:M) - User's orders
- → `recipe` (1:M) - User creates recipes
- → `meal_plan` (1:M) - User's meal plans
- → `recipe_review` (1:M) - User's reviews

---

### `user_role` (Role-Based Access Control)
```sql
CREATE TABLE user_role (
    user_id UUID NOT NULL,
    role_name VARCHAR(20) NOT NULL,
    PRIMARY KEY (user_id, role_name),
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
);
```

**Common Roles:**
- `User` - Default role (given on registration)
- `Admin` - Administrative privileges

**Indexes:**
- PRIMARY KEY on `(user_id, role_name)`
- INDEX on `user_id`

---

## 2. FRIDGE MANAGEMENT TABLES

### `fridge` (Shared refrigerators)
```sql
CREATE TABLE fridge (
    fridge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fridge_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Multiple users can share a fridge (e.g., roommates, family)

---

### `fridge_access` (Fridge sharing & permissions)
```sql
CREATE TABLE fridge_access (
    fridge_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'Owner' or 'Member'
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (fridge_id, user_id),
    FOREIGN KEY (fridge_id) REFERENCES fridge(fridge_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
);
```

**Roles:**
- `Owner` - Can delete fridge, manage members
- `Member` - Can view/modify inventory

**Indexes:**
- PRIMARY KEY on `(fridge_id, user_id)`
- INDEX on `user_id`

---

### `fridge_item` (Inventory in fridges - FIFO tracking)
```sql
CREATE TABLE fridge_item (
    fridge_id UUID NOT NULL,
    ingredient_id INT NOT NULL,
    batch_number SERIAL,
    quantity DECIMAL(10, 2) NOT NULL CHECK (quantity > 0),
    expiry_date DATE NOT NULL,
    added_date DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (fridge_id, ingredient_id, batch_number),
    FOREIGN KEY (fridge_id) REFERENCES fridge(fridge_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT
);
```

**Purpose:** Track ingredient batches with expiry dates for **FIFO consumption**

**Indexes:**
- PRIMARY KEY on `(fridge_id, ingredient_id, batch_number)`
- INDEX on `expiry_date` (for FIFO queries)

---

## 3. INVENTORY TABLE

### `ingredient` (Master ingredient catalog)
```sql
CREATE TABLE ingredient (
    ingredient_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    standard_unit VARCHAR(20) NOT NULL,  -- 'gram', 'ml', 'piece', etc.
    category VARCHAR(50)
);
```

**Examples:**
- (1, 'Milk', 'ml', 'Dairy')
- (2, 'Eggs', 'piece', 'Dairy')
- (3, 'Chicken Breast', 'gram', 'Meat')

**Indexes:**
- PRIMARY KEY on `ingredient_id`
- UNIQUE on `name`

---

## 4. RECIPE SYSTEM TABLES

### `recipe` (User-created recipes)
```sql
CREATE TABLE recipe (
    recipe_id SERIAL PRIMARY KEY,
    owner_id UUID NOT NULL,
    recipe_name VARCHAR(100) NOT NULL,
    description TEXT,
    cooking_time INT,  -- minutes
    status VARCHAR(30) NOT NULL DEFAULT 'Published',  -- 'Draft' or 'Published'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES "user"(user_id) ON DELETE CASCADE
);
```

**Indexes:**
- PRIMARY KEY on `recipe_id`
- INDEX on `owner_id`
- INDEX on `status`

---

### `recipe_requirement` (Ingredients needed for recipe)
```sql
CREATE TABLE recipe_requirement (
    recipe_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity_needed DECIMAL(10, 2) NOT NULL CHECK (quantity_needed > 0),
    PRIMARY KEY (recipe_id, ingredient_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT
);
```

**Example:**
- Recipe "Scrambled Eggs": requires 2 eggs, 50ml milk

**Indexes:**
- PRIMARY KEY on `(recipe_id, ingredient_id)`

---

### `recipe_step` (Cooking instructions)
```sql
CREATE TABLE recipe_step (
    recipe_id INT NOT NULL,
    step_number INT NOT NULL CHECK (step_number > 0),
    description TEXT NOT NULL,
    PRIMARY KEY (recipe_id, step_number),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE
);
```

**Indexes:**
- PRIMARY KEY on `(recipe_id, step_number)`

---

### `recipe_review` (User ratings & comments)
```sql
CREATE TABLE recipe_review (
    user_id UUID NOT NULL,
    recipe_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    review_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, recipe_id),
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE
);
```

**Constraints:**
- Rating must be 1-5 stars
- One review per user per recipe (can update)

**Indexes:**
- PRIMARY KEY on `(user_id, recipe_id)`
- INDEX on `recipe_id`

---

### `meal_plan` (Scheduled recipes)
```sql
CREATE TABLE meal_plan (
    plan_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    recipe_id INT NOT NULL,
    planned_date TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Planned',
    -- Status: 'Planned', 'Ready', 'Insufficient', 'Finished', 'Canceled'
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE
);
```

**Status Values:**
- `Planned` - Scheduled but >14 days away
- `Ready` - All ingredients available
- `Insufficient` - Missing ingredients
- `Finished` - Recipe has been cooked
- `Canceled` - User canceled

**Indexes:**
- PRIMARY KEY on `plan_id`
- INDEX on `(user_id, planned_date)`
- INDEX on `status`

---

## 5. PROCUREMENT TABLES

### `partner` (External suppliers)
```sql
CREATE TABLE partner (
    partner_id SERIAL PRIMARY KEY,
    partner_name VARCHAR(50) UNIQUE NOT NULL,
    contract_date DATE NOT NULL,
    avg_shipping_days INT NOT NULL CHECK (avg_shipping_days > 0),
    credit_score INT NOT NULL CHECK (credit_score >= 0 AND credit_score <= 100)
);
```

**Examples:**
- (1, 'FreshMart Wholesale', '2025-01-01', 3, 85)
- (2, 'Sunny Supplies', '2024-06-15', 5, 92)

**Indexes:**
- PRIMARY KEY on `partner_id`
- UNIQUE on `partner_name`

---

### `external_product` (Products from partners)
```sql
CREATE TABLE external_product (
    external_sku VARCHAR(50) PRIMARY KEY,
    partner_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL CHECK (current_price > 0),
    selling_unit VARCHAR(20) NOT NULL,  -- '1L Bottle', 'Pack of 12', etc.
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT
);
```

**Example:**
- ('FM-MILK-1L', 1, 1, 'Fresh Milk 1L', 4.99, '1L Bottle')

**Indexes:**
- PRIMARY KEY on `external_sku`
- INDEX on `ingredient_id`
- INDEX on `partner_id`

---

### `shopping_list_item` (User's shopping list)
```sql
CREATE TABLE shopping_list_item (
    user_id UUID NOT NULL,
    ingredient_id INT NOT NULL,
    quantity_to_buy DECIMAL(10, 2) NOT NULL CHECK (quantity_to_buy > 0),
    added_date DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, ingredient_id),
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT
);
```

**Note:** `needed_by` is NOT stored - computed dynamically from meal plans

**Indexes:**
- PRIMARY KEY on `(user_id, ingredient_id)`

---

### `store_order` (Orders placed with partners)
```sql
CREATE TABLE store_order (
    order_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    partner_id INT NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expected_arrival DATE,
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    order_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    -- Status: 'Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled'
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id) ON DELETE RESTRICT
);
```

**Indexes:**
- PRIMARY KEY on `order_id`
- INDEX on `user_id`
- INDEX on `order_status`
- INDEX on `order_date`

---

### `order_item` (Items in an order - with price snapshot)
```sql
CREATE TABLE order_item (
    order_id INT NOT NULL,
    external_sku VARCHAR(50) NOT NULL,
    partner_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    deal_price DECIMAL(10, 2) NOT NULL CHECK (deal_price > 0),  -- Price snapshot!
    PRIMARY KEY (order_id, external_sku),
    FOREIGN KEY (order_id) REFERENCES store_order(order_id) ON DELETE CASCADE,
    FOREIGN KEY (external_sku) REFERENCES external_product(external_sku) ON DELETE RESTRICT,
    FOREIGN KEY (partner_id) REFERENCES partner(partner_id) ON DELETE RESTRICT
);
```

**Important:** `deal_price` stores the price at time of order (immutable)

**Indexes:**
- PRIMARY KEY on `(order_id, external_sku)`

---

## 🔗 Key Relationships Summary

### Many-to-Many Relationships:
1. **User ↔ Role** via `user_role`
2. **User ↔ Fridge** via `fridge_access` (with role: Owner/Member)
3. **User ↔ Ingredient** via `shopping_list_item` (shopping list)
4. **Recipe ↔ Ingredient** via `recipe_requirement` (ingredients needed)
5. **Fridge ↔ Ingredient** via `fridge_item` (inventory with batches)

### One-to-Many Relationships:
- User → Recipe (user creates recipes)
- User → StoreOrder (user places orders)
- User → MealPlan (user schedules recipes)
- User → RecipeReview (user reviews recipes)
- Partner → ExternalProduct (partner sells products)
- Partner → StoreOrder (orders from partner)
- StoreOrder → OrderItem (items in order)
- Recipe → RecipeStep (cooking steps)

---

## 🎯 Database Features Demonstrated

✅ **Primary Keys:** All tables have appropriate PKs (serial, UUID, composite)
✅ **Foreign Keys:** Proper referential integrity with CASCADE/RESTRICT
✅ **Unique Constraints:** user_name, email, ingredient name, etc.
✅ **Check Constraints:** Quantities > 0, ratings 1-5, credit_score 0-100
✅ **Default Values:** Timestamps, UUIDs, statuses
✅ **Composite Keys:** Multi-column primary keys for junction tables
✅ **Indexes:** Strategic indexing on foreign keys and frequently queried columns
✅ **Data Types:** VARCHAR, INT, DECIMAL, UUID, DATE, TIMESTAMP, TEXT
✅ **CASCADE Deletes:** Maintain referential integrity
✅ **ON DELETE RESTRICT:** Prevent deletion of referenced data

---

## 📊 Table Row Count Examples

After running `generate_data.py`:

| Table | Expected Rows | Purpose |
|-------|---------------|---------|
| user | 500 | Test users |
| user_role | 500+ | User + some Admin |
| ingredient | 150 | Food items |
| fridge | 300 | Shared fridges |
| fridge_access | 600+ | User-fridge links |
| **fridge_item** | **50,000** | 🔥 Large table - inventory batches |
| recipe | 800 | User recipes |
| recipe_requirement | 3,200+ | Ingredients per recipe |
| recipe_step | 6,400+ | Cooking steps |
| **recipe_review** | **10,000** | 🔥 Large table - user ratings |
| **meal_plan** | **20,000** | 🔥 Large table - scheduled meals |
| partner | 20 | Suppliers |
| external_product | 800 | Products available |
| shopping_list_item | Variable | User shopping lists |
| store_order | 8,000 | Orders placed |
| order_item | 25,000 | Order line items |

**Total Records: ~120,000+**

---

This schema supports:
- Multi-user fridge sharing
- FIFO inventory management
- Recipe creation & meal planning
- Frontend-driven procurement
- Role-based access control
- Behavioral analytics (via MongoDB)
