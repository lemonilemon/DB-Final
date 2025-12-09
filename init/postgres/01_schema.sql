-- ============================================================================
-- NEW Fridge - PostgreSQL Database Schema
-- ============================================================================
-- Version: 1.0.0
-- Date: December 10, 2025
-- Description: Complete schema for smart inventory and procurement system
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- User Management
-- ============================================================================

-- User role enumeration
CREATE TYPE user_role_enum AS ENUM ('User', 'Admin');

-- User table
CREATE TABLE IF NOT EXISTS "user" (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_name VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(60) NOT NULL,  -- BCrypt hash
    email VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(10) NOT NULL DEFAULT 'Active',  -- Active, Disabled
    role user_role_enum NOT NULL DEFAULT 'User'
);

CREATE INDEX idx_user_name ON "user"(user_name);
CREATE INDEX idx_user_email ON "user"(email);

-- ============================================================================
-- Fridge Management
-- ============================================================================

-- Fridge table
CREATE TABLE IF NOT EXISTS fridge (
    fridge_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fridge_name VARCHAR(50) NOT NULL,
    description VARCHAR(200)
);

-- Fridge access control (multi-tenancy)
CREATE TABLE IF NOT EXISTS fridge_access (
    user_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    fridge_id UUID NOT NULL REFERENCES fridge(fridge_id) ON DELETE CASCADE,
    access_role VARCHAR(10) NOT NULL,  -- Owner, Member
    PRIMARY KEY (user_id, fridge_id)
);

-- ============================================================================
-- Inventory Management
-- ============================================================================

-- Ingredient catalog
CREATE TABLE IF NOT EXISTS ingredient (
    ingredient_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    standard_unit VARCHAR(10) NOT NULL,  -- g, ml, pcs
    shelf_life_days INTEGER NOT NULL CHECK (shelf_life_days > 0)
);

CREATE INDEX idx_ingredient_name ON ingredient(name);

-- Fridge inventory items
CREATE TABLE IF NOT EXISTS fridge_item (
    fridge_item_id BIGSERIAL PRIMARY KEY,
    fridge_id UUID NOT NULL REFERENCES fridge(fridge_id) ON DELETE CASCADE,
    ingredient_id BIGINT NOT NULL REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT,
    quantity NUMERIC(10, 2) NOT NULL CHECK (quantity >= 0),
    entry_date DATE NOT NULL,
    expiry_date DATE NOT NULL
);

CREATE INDEX idx_fridge_item_lookup ON fridge_item(fridge_id, ingredient_id);
CREATE INDEX idx_fridge_item_expiry ON fridge_item(fridge_id, expiry_date);

-- ============================================================================
-- Recipe Management
-- ============================================================================

-- User-created recipes
CREATE TABLE IF NOT EXISTS recipe (
    recipe_id BIGSERIAL PRIMARY KEY,
    owner_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE RESTRICT,
    recipe_name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    cooking_time INTEGER CHECK (cooking_time > 0),  -- minutes
    status VARCHAR(10) NOT NULL DEFAULT 'Published',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Recipe ingredients
CREATE TABLE IF NOT EXISTS recipe_requirement (
    recipe_id BIGINT NOT NULL REFERENCES recipe(recipe_id) ON DELETE CASCADE,
    ingredient_id BIGINT NOT NULL REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT,
    quantity_needed NUMERIC(10, 2) NOT NULL CHECK (quantity_needed > 0),
    PRIMARY KEY (recipe_id, ingredient_id)
);

-- Recipe cooking steps
CREATE TABLE IF NOT EXISTS recipe_step (
    recipe_id BIGINT NOT NULL REFERENCES recipe(recipe_id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    description VARCHAR(1000) NOT NULL,
    PRIMARY KEY (recipe_id, step_number)
);

-- Recipe reviews
CREATE TABLE IF NOT EXISTS recipe_review (
    user_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    recipe_id BIGINT NOT NULL REFERENCES recipe(recipe_id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment VARCHAR(500),
    review_date TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, recipe_id)
);

-- ============================================================================
-- Meal Planning
-- ============================================================================

-- Meal plans (scheduled recipes)
CREATE TABLE IF NOT EXISTS meal_plan (
    plan_id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    recipe_id BIGINT NOT NULL REFERENCES recipe(recipe_id) ON DELETE CASCADE,
    fridge_id UUID NOT NULL REFERENCES fridge(fridge_id) ON DELETE CASCADE,
    planned_date TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Planned'  -- Planned, Ready, Insufficient, Finished, Cancelled
);

CREATE INDEX idx_meal_plan_user_date ON meal_plan(user_id, planned_date);

-- ============================================================================
-- Procurement & Orders
-- ============================================================================

-- Partner (supplier) table
CREATE TABLE IF NOT EXISTS partner (
    partner_id BIGSERIAL PRIMARY KEY,
    partner_name VARCHAR(50) NOT NULL,
    contract_date DATE NOT NULL,
    avg_shipping_days INTEGER NOT NULL CHECK (avg_shipping_days > 0),
    credit_score INTEGER NOT NULL CHECK (credit_score >= 0 AND credit_score <= 100)
);

-- External products catalog
CREATE TABLE IF NOT EXISTS external_product (
    partner_id BIGINT NOT NULL REFERENCES partner(partner_id) ON DELETE RESTRICT,
    external_sku VARCHAR(50) NOT NULL,
    ingredient_id BIGINT NOT NULL REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT,
    product_name VARCHAR(100) NOT NULL,
    current_price NUMERIC(10, 2) NOT NULL CHECK (current_price > 0),
    selling_unit VARCHAR(20) NOT NULL,  -- e.g., "1L Bottle", "6-Pack"
    unit_quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00 CHECK (unit_quantity > 0),  -- Conversion ratio
    PRIMARY KEY (partner_id, external_sku)
);

CREATE INDEX idx_ext_prod_ing_price ON external_product(ingredient_id, current_price);

-- Shopping list (user cart)
CREATE TABLE IF NOT EXISTS shopping_list_item (
    user_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    ingredient_id BIGINT NOT NULL REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT,
    quantity_to_buy NUMERIC(10, 2) NOT NULL CHECK (quantity_to_buy > 0),
    added_date DATE NOT NULL,
    needed_by DATE,  -- Optional deadline
    PRIMARY KEY (user_id, ingredient_id)
);

-- Store orders
CREATE TABLE IF NOT EXISTS store_order (
    order_id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE RESTRICT,
    partner_id BIGINT NOT NULL REFERENCES partner(partner_id) ON DELETE RESTRICT,
    fridge_id UUID REFERENCES fridge(fridge_id) ON DELETE SET NULL,
    order_date TIMESTAMP NOT NULL,
    expected_arrival DATE,
    total_price NUMERIC(10, 2) NOT NULL CHECK (total_price >= 0),
    order_status VARCHAR(15) NOT NULL  -- Pending, Processing, Shipped, Delivered, Cancelled
);

CREATE INDEX idx_order_user_date ON store_order(user_id, order_date);

-- Order line items
CREATE TABLE IF NOT EXISTS order_item (
    order_id BIGINT NOT NULL REFERENCES store_order(order_id) ON DELETE CASCADE,
    external_sku VARCHAR(50) NOT NULL,
    partner_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    deal_price NUMERIC(10, 2) NOT NULL,  -- Price snapshot at order time
    PRIMARY KEY (order_id, external_sku),
    FOREIGN KEY (partner_id, external_sku) REFERENCES external_product(partner_id, external_sku)
);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE "user" IS 'User accounts with authentication and role management';
COMMENT ON TABLE fridge IS 'Shared fridges for multi-tenant inventory management';
COMMENT ON TABLE fridge_access IS 'Permission mapping for fridge access (Owner/Member roles)';
COMMENT ON TABLE ingredient IS 'Master ingredient catalog with standard units';
COMMENT ON TABLE fridge_item IS 'Fridge inventory items with FIFO expiry tracking';
COMMENT ON TABLE recipe IS 'User-created recipes with cooking instructions';
COMMENT ON TABLE recipe_requirement IS 'Ingredient requirements for recipes';
COMMENT ON TABLE recipe_step IS 'Step-by-step cooking instructions';
COMMENT ON TABLE recipe_review IS 'User ratings and reviews for recipes';
COMMENT ON TABLE meal_plan IS 'Scheduled recipes with automatic availability checking';
COMMENT ON TABLE partner IS 'Supplier/store partners with shipping information';
COMMENT ON TABLE external_product IS 'Products sold by partners with unit conversion';
COMMENT ON TABLE shopping_list_item IS 'User shopping cart with optional deadlines';
COMMENT ON TABLE store_order IS 'Purchase orders with split-by-partner logic';
COMMENT ON TABLE order_item IS 'Order line items with price snapshots';

COMMENT ON COLUMN external_product.unit_quantity IS 'Conversion ratio: quantity in standard_unit per selling unit (e.g., 1000ml per 1L bottle)';
COMMENT ON COLUMN shopping_list_item.needed_by IS 'Optional deadline for delivery validation';
COMMENT ON COLUMN meal_plan.status IS 'Auto-updated: Planned (>14 days), Ready (available), Insufficient (missing), Finished (cooked), Cancelled';
COMMENT ON COLUMN order_item.deal_price IS 'Price snapshot at order time (never use current_price for historical orders)';

-- ============================================================================
-- End of Schema
-- ============================================================================
