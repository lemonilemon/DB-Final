# Shopping List Workflow Summary

## Overview

The shopping list feature serves as a personal cart where users can add ingredients they need to purchase. It's designed to integrate with the fridge inventory and procurement system.

---

## Database Schema

### ShoppingListItem Table
```sql
CREATE TABLE shopping_list_item (
    user_id UUID NOT NULL,              -- FK to user (composite PK)
    ingredient_id BIGINT NOT NULL,       -- FK to ingredient (composite PK)
    quantity_to_buy NUMERIC(10,2) NOT NULL CHECK (quantity_to_buy > 0),
    added_date DATE NOT NULL,
    PRIMARY KEY (user_id, ingredient_id),
    FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredient(ingredient_id) ON DELETE RESTRICT
);
```

**Key Points:**
- Composite primary key: (user_id, ingredient_id)
- One item per ingredient per user (updating replaces quantity)
- Quantities in ingredient's standard unit (g, ml, pcs)
- Cascade delete when user is deleted

---

## API Endpoints

### 1. Add Item to Shopping List
**POST /api/shopping-list**

Adds an ingredient to the user's shopping list or updates quantity if already exists.

**Request:**
```json
{
  "ingredient_id": 5,
  "quantity_to_buy": 500.00
}
```

**Response:**
```json
{
  "message": "Item added to shopping list",
  "detail": "Added ingredient #5"
}
```

**Behavior:**
- If ingredient already in list → **UPDATE** quantity and date
- If ingredient not in list → **INSERT** new item
- Validates ingredient exists
- Sets added_date to current date

---

### 2. View Shopping List
**GET /api/shopping-list**

Retrieves user's shopping list with ingredient details and product availability.

**Response:**
```json
[
  {
    "ingredient_id": 5,
    "ingredient_name": "Milk",
    "quantity_to_buy": 500.00,
    "standard_unit": "ml",
    "added_date": "2025-12-08",
    "available_products_count": 3
  },
  {
    "ingredient_id": 12,
    "ingredient_name": "Eggs",
    "quantity_to_buy": 12.00,
    "standard_unit": "pcs",
    "added_date": "2025-12-07",
    "available_products_count": 5
  }
]
```

**Features:**
- Sorted by added_date (newest first)
- Shows how many external products available for each ingredient
- Includes ingredient details (name, unit)
- Ready to convert into orders

---

### 3. Remove Item from Shopping List
**DELETE /api/shopping-list/{ingredient_id}**

Removes a specific ingredient from the shopping list.

**Response:**
```json
{
  "message": "Item removed from shopping list",
  "detail": "Removed ingredient #5"
}
```

**Behavior:**
- Returns 404 if item not in list
- Permanent deletion (no soft delete)

---

## Workflow Integration

### Typical User Journey

```
1. Check Fridge Inventory
   ↓
   User sees they're low on milk (200ml left, expires soon)
   ↓
2. Add to Shopping List
   POST /api/shopping-list
   { "ingredient_id": 5, "quantity_to_buy": 1000 }
   ↓
3. View Shopping List
   GET /api/shopping-list
   Shows: Milk (1000ml), Eggs (12pcs), etc.
   ↓
4. Get Product Recommendations
   GET /api/products/recommendations?ingredient_id=5&quantity_needed=1000&needed_by=2025-12-15
   Returns: Best products with delivery dates
   ↓
5. Create Order
   POST /api/orders
   { "fridge_id": "...", "items": [{"external_sku": "FM-MILK-1L", "quantity": 1}] }
   ↓
6. Shopping List Item Auto-removed or Manually Removed
   DELETE /api/shopping-list/5
```

---

## Business Logic (Service Layer)

### Add to Shopping List
```python
async def add_to_shopping_list(
    request: ShoppingListAddRequest,
    current_user_id: UUID,
    session: AsyncSession
) -> None:
    # 1. Verify ingredient exists
    # 2. Check if item already in shopping list
    #    - If exists: UPDATE quantity and added_date
    #    - If not exists: INSERT new item
    # 3. Commit transaction
```

**Key Features:**
- Upsert pattern (INSERT or UPDATE)
- Ingredient validation
- Uses merge() for efficient upsert

---

### Get Shopping List
```python
async def get_shopping_list(
    current_user_id: UUID,
    session: AsyncSession
) -> List[ShoppingListItemResponse]:
    # 1. Join shopping_list_item with ingredient
    # 2. For each item, count available external_products
    # 3. Sort by added_date DESC
    # 4. Return enriched response
```

**Query Optimization:**
- Single JOIN for ingredient details
- Separate query for product count (could be optimized with subquery)
- Sorted by date for better UX

---

### Remove from Shopping List
```python
async def remove_from_shopping_list(
    ingredient_id: int,
    current_user_id: UUID,
    session: AsyncSession
) -> None:
    # 1. Find item by (user_id, ingredient_id)
    # 2. If not found: raise 404
    # 3. Delete item
    # 4. Commit
```

---

## Integration Points

### 1. Availability Check Integration
Users can check if fridge has enough ingredients for a recipe:
```
GET /api/availability/check?recipe_id=1&fridge_id=...&needed_by=2025-12-15
```
This shows what's missing → User adds missing items to shopping list

### 2. Product Recommendations Integration
For each shopping list item, get best products:
```
GET /api/products/recommendations?ingredient_id=5&quantity_needed=1000&needed_by=2025-12-15
```
Returns products sorted by price with delivery validation

### 3. Order Creation Integration
Convert shopping list to order:
```
POST /api/orders
{
  "fridge_id": "...",
  "items": [
    {"external_sku": "FM-MILK-1L", "quantity": 1},
    {"external_sku": "SS-EGGS-12", "quantity": 1}
  ]
}
```

**Note:** Currently, removing from shopping list after order creation is **manual**.
**Future Enhancement:** Auto-remove items after successful order creation.

---

## Current Limitations & Future Enhancements

### Current Limitations:
1. **No Auto-removal:** Items not automatically removed after ordering
2. **No Quantities Tracking:** Doesn't track if partial quantities ordered
3. **No Multi-fridge Support:** Shopping list is per-user, not per-fridge
4. **No Sharing:** Can't share shopping lists between fridge members

### Proposed Enhancements:
1. **Auto-removal on Order:**
   - When order created, remove ordered items from shopping list
   - Or mark as "ordered" with order_id reference

2. **Quantity Tracking:**
   - Track quantity_ordered vs quantity_needed
   - Allow partial ordering

3. **Shopping List Categories:**
   - Group by ingredient type (dairy, produce, etc.)
   - Priority levels (urgent, normal, low)

4. **Fridge-specific Lists:**
   - Shopping list per fridge instead of per user
   - Collaborative lists for shared fridges

5. **Smart Suggestions:**
   - Based on frequently purchased items
   - Based on expiring fridge items
   - Based on meal plans

---

## Data Flow Diagram

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ├─── POST /api/shopping-list ────┐
       │                                  │
       ├─── GET /api/shopping-list ──────┤
       │                                  │
       └─── DELETE /api/shopping-list/id ┤
                                          │
                                          ▼
                                 ┌────────────────┐
                                 │  Shopping List │
                                 │    Service     │
                                 └────────┬───────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
            ┌───────────────┐    ┌──────────────┐    ┌─────────────────┐
            │ shopping_list │    │  ingredient  │    │ external_product│
            │     _item     │    │              │    │                 │
            └───────────────┘    └──────────────┘    └─────────────────┘
```

---

## Example Use Cases

### Use Case 1: Weekly Grocery Planning
```
1. User checks fridge inventory (GET /api/fridges/{id}/items)
2. Identifies low/expiring items
3. Adds items to shopping list (POST /api/shopping-list)
4. Views complete list (GET /api/shopping-list)
5. Gets recommendations for each item
6. Creates order with selected products
```

### Use Case 2: Recipe-based Shopping
```
1. User wants to cook Spaghetti Carbonara
2. Checks availability (GET /api/availability/check?recipe_id=2)
3. System shows: Need 200g pasta, 2 eggs
4. User adds missing ingredients to shopping list
5. Proceeds to order
```

### Use Case 3: Bulk Shopping
```
1. User adds multiple items throughout the week
2. Shopping list accumulates items
3. On weekend, user reviews full list
4. Removes unwanted items (DELETE)
5. Creates single order with all items
```

---

## Security & Permissions

- **Authentication Required:** All endpoints require valid JWT token
- **User Isolation:** Users can only see/modify their own shopping list
- **No Admin Override:** Even admins can't modify other users' shopping lists
- **Ingredient Validation:** Prevents adding non-existent ingredients
- **Cascade Delete:** Shopping list cleared when user deleted

---

## Performance Considerations

### Current Implementation:
- **Indexes:** Primary key index on (user_id, ingredient_id)
- **Query Count:** 2 queries per shopping list view (items + product counts)
- **Scalability:** O(n) where n = items in user's shopping list (typically < 50)

### Optimization Opportunities:
1. **Single Query with Subquery:**
   ```sql
   SELECT sl.*, i.*,
          (SELECT COUNT(*) FROM external_product WHERE ingredient_id = sl.ingredient_id) as product_count
   FROM shopping_list_item sl
   JOIN ingredient i ON sl.ingredient_id = i.ingredient_id
   WHERE sl.user_id = ?
   ```

2. **Caching:**
   - Cache product counts (rarely change)
   - Cache ingredient details (static data)

3. **Batch Operations:**
   - Add multiple items in one request
   - Remove multiple items in one request

---

## Testing

### Test Scenarios:
1. ✅ Add item to empty shopping list
2. ✅ Update existing item quantity
3. ✅ Remove item from shopping list
4. ✅ View shopping list with product counts
5. ✅ Add invalid ingredient (should fail)
6. ✅ Remove non-existent item (should fail 404)
7. ✅ Add item with invalid quantity (should fail validation)
8. ✅ Shopping list isolation (user A can't see user B's list)

---

## Summary

The shopping list is a **simple, user-centric cart system** that:
- Stores desired ingredients per user
- Integrates with fridge inventory and ordering
- Uses upsert pattern for easy updates
- Provides product availability information
- Serves as a bridge between "need to buy" and "actually ordering"

**Current Status:** ✅ Fully functional with basic CRUD operations
**Next Steps:** Consider auto-removal on order creation and multi-fridge support
