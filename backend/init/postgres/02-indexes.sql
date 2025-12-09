-- =========================================================
-- 資料庫索引優化腳本 (Database Indexing Optimization)
-- 適用於: NEW Fridge Schema v2.0
-- =========================================================

-- 1. 針對 Foreign Keys 建立索引 (加速 JOIN 與 CASCADE DELETE)
-- PostgreSQL 預設不會為 FK 建立索引，手動建立可大幅提升關聯查詢效能
-- ---------------------------------------------------------

-- User & Fridge Access
CREATE INDEX IF NOT EXISTS idx_fridge_access_user_id ON fridge_access(user_id);
CREATE INDEX IF NOT EXISTS idx_fridge_access_fridge_id ON fridge_access(fridge_id);

-- Fridge Items (庫存查詢高頻區)
CREATE INDEX IF NOT EXISTS idx_fridge_item_fridge_id ON fridge_item(fridge_id);
CREATE INDEX IF NOT EXISTS idx_fridge_item_ingredient_id ON fridge_item(ingredient_id);

-- External Products (供應鏈)
CREATE INDEX IF NOT EXISTS idx_ext_prod_partner_id ON external_product(partner_id);
CREATE INDEX IF NOT EXISTS idx_ext_prod_ingredient_id ON external_product(ingredient_id);

-- Shopping List
CREATE INDEX IF NOT EXISTS idx_shopping_user_id ON shopping_list_item(user_id);
CREATE INDEX IF NOT EXISTS idx_shopping_ingredient_id ON shopping_list_item(ingredient_id);

-- Orders (訂單關聯)
CREATE INDEX IF NOT EXISTS idx_order_user_id ON store_order(user_id);
CREATE INDEX IF NOT EXISTS idx_order_partner_id ON store_order(partner_id);
CREATE INDEX IF NOT EXISTS idx_order_fridge_id ON store_order(fridge_id); -- 支援查詢「某冰箱的補貨紀錄」

-- Order Items
CREATE INDEX IF NOT EXISTS idx_order_item_order_id ON order_item(order_id);
-- 複合 FK 索引 (對應 External Product 的複合 PK)
CREATE INDEX IF NOT EXISTS idx_order_item_product_ref ON order_item(partner_id, external_sku);

-- Recipes
CREATE INDEX IF NOT EXISTS idx_recipe_owner_id ON recipe(owner_id);
CREATE INDEX IF NOT EXISTS idx_recipe_req_recipe_id ON recipe_requirement(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_req_ingredient_id ON recipe_requirement(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_recipe_step_recipe_id ON recipe_step(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_review_recipe_id ON recipe_review(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_review_user_id ON recipe_review(user_id);

-- Meal Plans
CREATE INDEX IF NOT EXISTS idx_meal_plan_user_id ON meal_plan(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_recipe_id ON meal_plan(recipe_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_fridge_id ON meal_plan(fridge_id);


-- 2. 針對 業務邏輯與搜尋 建立索引 (Business Logic Optimization)
-- ---------------------------------------------------------

-- [重要] FIFO 扣庫存優化
-- 說明：系統需頻繁查詢「某冰箱、某食材、最早過期」的批次。
-- 複合索引：先篩選 fridge+ingredient，再依 expiry_date 排序
-- (注意：Python 程式碼中可能有部分重複定義，但 SQL 層面明確建立更保險)
CREATE INDEX IF NOT EXISTS idx_fridge_item_fifo ON fridge_item(fridge_id, ingredient_id, expiry_date ASC);

-- [重要] 過期預警優化
-- 說明：系統需每天掃描「快過期」的食材
CREATE INDEX IF NOT EXISTS idx_fridge_item_expiry ON fridge_item(expiry_date);

-- [搜尋] 食譜名稱搜尋
-- 說明：加速使用者輸入關鍵字找食譜 (支援 Like 'Keyword%')
CREATE INDEX IF NOT EXISTS idx_recipe_name_search ON recipe(recipe_name);

-- [篩選] 訂單狀態與時間
-- 說明：Admin 後台常需篩選「待處理」訂單或依時間排序
CREATE INDEX IF NOT EXISTS idx_order_status ON store_order(order_status);
CREATE INDEX IF NOT EXISTS idx_order_date ON store_order(order_date DESC);

-- [計畫] 餐點計畫查詢
-- 說明：使用者通常查看「特定日期範圍」的計畫
CREATE INDEX IF NOT EXISTS idx_meal_plan_date ON meal_plan(planned_date);

-- [審核] 食譜狀態
-- 說明：Admin 篩選 'Pending' 狀態的食譜
CREATE INDEX IF NOT EXISTS idx_recipe_status ON recipe(status);