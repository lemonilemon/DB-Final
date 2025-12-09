-- ============================================================================
-- NEW Fridge - Optimized Index Strategy
-- ============================================================================
-- Version: 2.0.0
-- Date: December 10, 2025
-- Description: Strategic indexes for high-performance queries
-- ============================================================================

-- ============================================================================
-- 1. 外部鍵索引 (Foreign Key Indexes)
-- ============================================================================
-- PostgreSQL 不會自動為外部鍵建立索引，需手動建立以優化 JOIN 效能

-- Fridge Item Foreign Keys
CREATE INDEX IF NOT EXISTS idx_fridge_item_fridge_id
    ON fridge_item(fridge_id);

CREATE INDEX IF NOT EXISTS idx_fridge_item_ingredient_id
    ON fridge_item(ingredient_id);

-- Meal Plan Foreign Keys
CREATE INDEX IF NOT EXISTS idx_meal_plan_user_id
    ON meal_plan(user_id);

CREATE INDEX IF NOT EXISTS idx_meal_plan_recipe_id
    ON meal_plan(recipe_id);

CREATE INDEX IF NOT EXISTS idx_meal_plan_fridge_id
    ON meal_plan(fridge_id);

-- Store Order Foreign Keys
CREATE INDEX IF NOT EXISTS idx_store_order_user_id
    ON store_order(user_id);

CREATE INDEX IF NOT EXISTS idx_store_order_fridge_id
    ON store_order(fridge_id);

CREATE INDEX IF NOT EXISTS idx_store_order_partner_id
    ON store_order(partner_id);

-- Order Item Foreign Keys
CREATE INDEX IF NOT EXISTS idx_order_item_order_id
    ON order_item(order_id);

-- Recipe Requirement Foreign Keys
CREATE INDEX IF NOT EXISTS idx_recipe_requirement_recipe_id
    ON recipe_requirement(recipe_id);

CREATE INDEX IF NOT EXISTS idx_recipe_requirement_ingredient_id
    ON recipe_requirement(ingredient_id);

-- Recipe Step Foreign Key
CREATE INDEX IF NOT EXISTS idx_recipe_step_recipe_id
    ON recipe_step(recipe_id);

-- Recipe Review Foreign Keys
CREATE INDEX IF NOT EXISTS idx_recipe_review_recipe_id
    ON recipe_review(recipe_id);

-- Fridge Access Foreign Keys
CREATE INDEX IF NOT EXISTS idx_fridge_access_fridge_id
    ON fridge_access(fridge_id);

-- Shopping List Foreign Key
CREATE INDEX IF NOT EXISTS idx_shopping_list_user_id
    ON shopping_list_item(user_id);

CREATE INDEX IF NOT EXISTS idx_shopping_list_ingredient_id
    ON shopping_list_item(ingredient_id);

-- External Product Foreign Key
CREATE INDEX IF NOT EXISTS idx_external_product_ingredient_id
    ON external_product(ingredient_id);

-- ============================================================================
-- 2. FIFO 複合索引 (FIFO Composite Index)
-- ============================================================================
-- 用於優化「先進先出」庫存扣減邏輯
-- 支援查詢: WHERE fridge_id = ? AND ingredient_id = ? ORDER BY expiry_date ASC

CREATE INDEX IF NOT EXISTS idx_fridge_item_fifo
    ON fridge_item (fridge_id, ingredient_id, expiry_date ASC);

COMMENT ON INDEX idx_fridge_item_fifo IS
    'FIFO composite index for inventory consumption: (fridge + ingredient + expiry_date)';

-- ============================================================================
-- 3. 查詢優化複合索引 (Query-Specific Composite Indexes)
-- ============================================================================

-- Meal Plan: User's meal plans for a specific fridge
CREATE INDEX IF NOT EXISTS idx_meal_plan_user_fridge
    ON meal_plan(user_id, fridge_id);

-- Meal Plan: Date range queries (calendar view)
CREATE INDEX IF NOT EXISTS idx_meal_plan_planned_date
    ON meal_plan(planned_date);

-- Meal Plan: Status filtering (find Insufficient plans)
CREATE INDEX IF NOT EXISTS idx_meal_plan_status
    ON meal_plan(status);

-- Meal Plan: Fridge + Date (for fridge-specific timeline)
CREATE INDEX IF NOT EXISTS idx_meal_plan_fridge_date
    ON meal_plan(fridge_id, planned_date);

-- Store Order: User + Date (order history chronological view)
CREATE INDEX IF NOT EXISTS idx_store_order_user_date
    ON store_order(user_id, order_date DESC);

-- Store Order: Fridge + Status (track fridge's pending orders)
CREATE INDEX IF NOT EXISTS idx_store_order_fridge_status
    ON store_order(fridge_id, order_status);

-- Store Order: Expected arrival (for timeline simulation)
CREATE INDEX IF NOT EXISTS idx_store_order_arrival
    ON store_order(expected_arrival)
    WHERE order_status IN ('Pending', 'Processing', 'Shipped');

-- External Product: Ingredient + Price (find cheapest product)
CREATE INDEX IF NOT EXISTS idx_external_product_ingredient_price
    ON external_product(ingredient_id, current_price ASC);

-- Shopping List: User + Needed By (deadline-based sorting)
CREATE INDEX IF NOT EXISTS idx_shopping_list_user_deadline
    ON shopping_list_item(user_id, needed_by);

-- ============================================================================
-- 4. 全文檢索索引 (Text Search Indexes)
-- ============================================================================

-- Recipe Name Search (using GIN for pattern matching)
CREATE INDEX IF NOT EXISTS idx_recipe_name_trgm
    ON recipe USING gin(recipe_name gin_trgm_ops);

-- Ingredient Name Search
CREATE INDEX IF NOT EXISTS idx_ingredient_name_trgm
    ON ingredient USING gin(name gin_trgm_ops);

-- Note: Requires pg_trgm extension
-- Run: CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- 5. 部分索引 (Partial Indexes)
-- ============================================================================
-- 只索引常用的資料子集，節省空間並提升效能

-- Active Meal Plans (exclude Finished and Cancelled)
CREATE INDEX IF NOT EXISTS idx_meal_plan_active
    ON meal_plan(user_id, planned_date)
    WHERE status NOT IN ('Finished', 'Cancelled');

-- Pending Orders (only active orders)
CREATE INDEX IF NOT EXISTS idx_store_order_pending
    ON store_order(user_id, expected_arrival)
    WHERE order_status IN ('Pending', 'Processing', 'Shipped');

-- Items Expiring Soon (next 30 days)
CREATE INDEX IF NOT EXISTS idx_fridge_item_expiring_soon
    ON fridge_item(fridge_id, expiry_date)
    WHERE expiry_date <= CURRENT_DATE + INTERVAL '30 days';

-- ============================================================================
-- Index Statistics and Comments
-- ============================================================================

COMMENT ON INDEX idx_fridge_item_fifo IS
    'Critical for FIFO inventory consumption performance';

COMMENT ON INDEX idx_meal_plan_user_fridge IS
    'Optimizes meal plan list queries by user and fridge';

COMMENT ON INDEX idx_external_product_ingredient_price IS
    'Enables fast cheapest-product lookup for procurement';

COMMENT ON INDEX idx_store_order_arrival IS
    'Partial index for timeline simulation (only active orders)';

COMMENT ON INDEX idx_meal_plan_active IS
    'Partial index excluding historical meal plans';

-- ============================================================================
-- Performance Notes
-- ============================================================================

-- Index Strategy Summary:
-- 1. All foreign keys indexed for JOIN performance
-- 2. FIFO composite index for core inventory logic
-- 3. Composite indexes for common multi-column queries
-- 4. Partial indexes to reduce index size and improve write performance
-- 5. Text search indexes for recipe/ingredient search (requires pg_trgm)

-- Maintenance:
-- - Run ANALYZE after bulk data load
-- - Consider REINDEX if fragmentation occurs
-- - Monitor index usage with pg_stat_user_indexes

-- ============================================================================
-- End of Indexes
-- ============================================================================
