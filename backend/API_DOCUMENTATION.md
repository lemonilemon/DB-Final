# NEW Fridge API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`
**Backend:** FastAPI + PostgreSQL + MongoDB

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Reference](#api-reference)
   - [Authentication APIs](#authentication-apis)
   - [Fridge Management APIs](#fridge-management-apis)
   - [Inventory Management APIs](#inventory-management-apis)
   - [Procurement APIs](#procurement-apis)
   - [Recipe APIs](#recipe-apis)
   - [Meal Planning APIs](#meal-planning-apis)
4. [Workflows](#workflows)
5. [Common Patterns](#common-patterns)
6. [Error Handling](#error-handling)

---

## Overview

NEW Fridge is a smart inventory and procurement management system with:
- **Shared Fridges**: Multiple users can share fridges (Owner/Member roles)
- **FIFO Consumption**: Automatically uses earliest expiring items first
- **Smart Procurement**: Frontend-driven ordering with delivery validation
- **Meal Planning**: Schedule recipes with automatic availability checks
- **Timeline Simulation**: Predicts ingredient availability considering future meal plans

---

## Authentication

### How It Works

1. **Register** → Get account
2. **Login** → Get JWT token
3. **Use token** in `Authorization` header for all protected endpoints

### Token Format

```
Authorization: Bearer <jwt_token>
```

**Token expires in:** 24 hours

---

## API Reference

### Authentication APIs

#### 1. Register

```http
POST /api/auth/register
```

**Request:**
```json
{
  "user_name": "alice",
  "email": "alice@example.com",
  "password": "secure_password"
}
```

**Response:** `201 Created`
```json
{
  "message": "User registered successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

#### 2. Login

```http
POST /api/auth/login
```

**Request:**
```json
{
  "user_name": "alice",
  "password": "secure_password"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save this token!** Use it in all subsequent requests.

---

#### 3. Get Current User

```http
GET /api/me
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_name": "alice",
  "email": "alice@example.com",
  "status": "Active",
  "roles": ["General User"]
}
```

---

### Fridge Management APIs

#### 1. Create Fridge

```http
POST /api/fridges
Authorization: Bearer <token>
```

**Request:**
```json
{
  "fridge_name": "Kitchen Fridge",
  "description": "Main fridge in the kitchen"
}
```

**Response:** `201 Created`
```json
{
  "fridge_id": "123e4567-e89b-12d3-a456-426614174000",
  "creator_id": "550e8400-e29b-41d4-a716-446655440000",
  "fridge_name": "Kitchen Fridge",
  "description": "Main fridge in the kitchen",
  "your_role": "Owner"
}
```

**Note:** You automatically become the Owner.

---

#### 2. List Your Fridges

```http
GET /api/fridges
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "fridge_id": "123e4567-e89b-12d3-a456-426614174000",
    "fridge_name": "Kitchen Fridge",
    "description": "Main fridge",
    "your_role": "Owner"
  },
  {
    "fridge_id": "987e6543-e21b-41d4-a716-446655440000",
    "fridge_name": "Roommate Fridge",
    "description": "Shared fridge",
    "your_role": "Member"
  }
]
```

---

#### 3. Invite Member (Owner Only)

```http
POST /api/fridges/{fridge_id}/members
Authorization: Bearer <token>
```

**Request:**
```json
{
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "role": "Member"
}
```

**Roles:** `"Owner"` or `"Member"`

**Response:** `201 Created`
```json
{
  "message": "Member added successfully"
}
```

**Permission:** Only Owners can add members.

---

#### 4. Remove Member (Owner Only)

```http
DELETE /api/fridges/{fridge_id}/members/{user_id}
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "message": "Member removed successfully"
}
```

---

### Inventory Management APIs

#### 1. Create Ingredient (Global Catalog)

```http
POST /api/ingredients
Authorization: Bearer <token>
```

**Request:**
```json
{
  "name": "Milk",
  "standard_unit": "ml",
  "category": "Dairy"
}
```

**Response:** `201 Created`
```json
{
  "ingredient_id": 1,
  "name": "Milk",
  "standard_unit": "ml",
  "category": "Dairy"
}
```

---

#### 2. List All Ingredients

```http
GET /api/ingredients
```

**Response:** `200 OK`
```json
[
  {
    "ingredient_id": 1,
    "name": "Milk",
    "standard_unit": "ml",
    "category": "Dairy"
  },
  {
    "ingredient_id": 2,
    "name": "Eggs",
    "standard_unit": "unit",
    "category": "Protein"
  }
]
```

---

#### 3. Add Items to Fridge

```http
POST /api/fridges/{fridge_id}/items
Authorization: Bearer <token>
```

**Request:**
```json
{
  "ingredient_id": 1,
  "quantity": 1000,
  "expiry_date": "2025-12-15"
}
```

**Response:** `201 Created`
```json
{
  "message": "Item added to fridge",
  "item_id": 123
}
```

**Note:** Each item is a separate batch with its own expiry date.

---

#### 4. View Fridge Inventory

```http
GET /api/fridges/{fridge_id}/items
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "ingredient_id": 1,
    "ingredient_name": "Milk",
    "standard_unit": "ml",
    "total_quantity": 1500,
    "items": [
      {
        "item_id": 101,
        "quantity": 500,
        "entry_date": "2025-12-01",
        "expiry_date": "2025-12-10"
      },
      {
        "item_id": 102,
        "quantity": 1000,
        "entry_date": "2025-12-07",
        "expiry_date": "2025-12-15"
      }
    ]
  }
]
```

**Note:** Items are grouped by ingredient, sorted by expiry date.

---

#### 5. Consume Ingredients (FIFO)

```http
POST /api/fridges/{fridge_id}/consume
Authorization: Bearer <token>
```

**Request:**
```json
{
  "ingredient_id": 1,
  "quantity": 750
}
```

**Response:** `200 OK`
```json
{
  "ingredient_name": "Milk",
  "requested_quantity": 750,
  "consumed_quantity": 750,
  "remaining_quantity": 750,
  "items_consumed": 2,
  "message": "Consumed 750.00 ml of Milk using FIFO (2 items affected)"
}
```

**FIFO Logic:** Always consumes from earliest expiring items first.

**Example:**
- Have: 500ml (exp Dec 10) + 1000ml (exp Dec 15)
- Consume: 750ml
- Result: Uses all 500ml from Dec 10 + 250ml from Dec 15

---

### Procurement APIs

#### 1. Create Partner

```http
POST /api/partners
Authorization: Bearer <token>
```

**Request:**
```json
{
  "partner_name": "SuperStore",
  "contract_date": "2025-01-01",
  "avg_shipping_days": 3,
  "credit_score": 85
}
```

**Response:** `201 Created`
```json
{
  "partner_id": 1,
  "partner_name": "SuperStore",
  "contract_date": "2025-01-01",
  "avg_shipping_days": 3,
  "credit_score": 85
}
```

---

#### 2. List Partners

```http
GET /api/partners
```

**Response:** `200 OK`
```json
[
  {
    "partner_id": 1,
    "partner_name": "SuperStore",
    "contract_date": "2025-01-01",
    "avg_shipping_days": 3,
    "credit_score": 85
  }
]
```

---

#### 3. Create Product

```http
POST /api/products
Authorization: Bearer <token>
```

**Request:**
```json
{
  "external_sku": "SS-MILK-1L",
  "partner_id": 1,
  "ingredient_id": 1,
  "product_name": "Fresh Milk 1L",
  "current_price": 42.00,
  "selling_unit": "1L Bottle"
}
```

**Response:** `201 Created`
```json
{
  "external_sku": "SS-MILK-1L",
  "partner_id": 1,
  "partner_name": "SuperStore",
  "ingredient_id": 1,
  "ingredient_name": "Milk",
  "product_name": "Fresh Milk 1L",
  "current_price": 42.00,
  "selling_unit": "1L Bottle"
}
```

---

#### 4. Check Availability ⭐ NEW

```http
GET /api/availability/check?recipe_id=1&fridge_id=<uuid>&needed_by=2025-12-15
Authorization: Bearer <token>
```

**Query Parameters:**
- `recipe_id` (required): Recipe to check
- `fridge_id` (required): Fridge to check against
- `needed_by` (required): Date when ingredients are needed (YYYY-MM-DD)

**Response:** `200 OK`

**Case 1: All available**
```json
{
  "all_available": true,
  "missing_ingredients": [],
  "message": "All ingredients available"
}
```

**Case 2: Missing ingredients**
```json
{
  "all_available": false,
  "missing_ingredients": [
    {
      "ingredient_id": 1,
      "ingredient_name": "Milk",
      "standard_unit": "ml",
      "shortage": 300,
      "needed_by": "2025-12-12"
    }
  ],
  "message": "1 ingredient(s) insufficient"
}
```

**Important Fields:**
- `shortage`: Minimum amount to order (fixes entire timeline)
- `needed_by`: **Computed** - earliest date when shortage occurs (order must arrive before this!)

**How It Works:**
1. Simulates fridge timeline with FIFO consumption
2. Considers all meal plans from fridge users (within 14 days)
3. Handles expiration dates
4. Returns **only** missing ingredients
5. Computes exact shortage and deadline

---

#### 5. Get Product Recommendations ⭐ NEW

```http
GET /api/products/recommendations?ingredient_id=1&quantity_needed=300&needed_by=2025-12-15
```

**Query Parameters:**
- `ingredient_id` (required): Ingredient to buy
- `quantity_needed` (required): How much needed
- `needed_by` (required): Delivery deadline (YYYY-MM-DD)

**Response:** `200 OK`
```json
{
  "ingredient_id": 1,
  "ingredient_name": "Milk",
  "quantity_needed": 300,
  "needed_by": "2025-12-15",
  "products": [
    {
      "external_sku": "SS-MILK-1L",
      "partner_id": 1,
      "partner_name": "SuperStore",
      "product_name": "Fresh Milk 1L",
      "current_price": 42.00,
      "selling_unit": "1L Bottle",
      "avg_shipping_days": 3,
      "expected_arrival": "2025-12-10"
    },
    {
      "external_sku": "FM-MILK-1L",
      "partner_id": 2,
      "partner_name": "FreshMart",
      "product_name": "Fresh Milk 1L",
      "current_price": 45.50,
      "selling_unit": "1L Bottle",
      "avg_shipping_days": 2,
      "expected_arrival": "2025-12-09"
    }
  ],
  "message": "Found 2 product(s) that arrive by 2025-12-15"
}
```

**Key Points:**
- Products **sorted by price** (cheapest first)
- **Only shows products that arrive in time** (expected_arrival <= needed_by)
- Returns **404** if no products can arrive in time
- First product is always cheapest option

**Expected Arrival Calculation:**
```
expected_arrival = today + avg_shipping_days
```

---

#### 6. Create Order ⭐ REDESIGNED

```http
POST /api/orders
Authorization: Bearer <token>
```

**Request:**
```json
{
  "fridge_id": "123e4567-e89b-12d3-a456-426614174000",
  "items": [
    {
      "external_sku": "SS-MILK-1L",
      "quantity": 1
    }
  ]
}
```

**Constraints:**
- All items **must be from same partner**
- If items from different partners, returns 400 error

**Response:** `201 Created`
```json
{
  "order_id": 1,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "partner_id": 1,
  "partner_name": "SuperStore",
  "order_date": "2025-12-07T10:30:00",
  "expected_arrival": "2025-12-10",
  "total_price": 42.00,
  "order_status": "Pending",
  "items": [
    {
      "external_sku": "SS-MILK-1L",
      "product_name": "Fresh Milk 1L",
      "partner_name": "SuperStore",
      "quantity": 1,
      "deal_price": 42.00,
      "subtotal": 42.00
    }
  ]
}
```

**Note:** `deal_price` is a price snapshot (saved at order time, won't change if partner updates price later).

---

#### 7. View Orders

```http
GET /api/orders
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "order_id": 1,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "partner_id": 1,
    "partner_name": "SuperStore",
    "order_date": "2025-12-07T10:30:00",
    "expected_arrival": "2025-12-10",
    "total_price": 42.00,
    "order_status": "Pending",
    "items": [...]
  }
]
```

**Order Status Values:**
- `Pending`: Order placed, waiting
- `Processing`: Being prepared
- `Shipped`: On the way
- `Delivered`: Arrived
- `Cancelled`: Order cancelled

---

#### 8. Update Order Status

```http
PUT /api/orders/{order_id}/status
Authorization: Bearer <token>
```

**Request:**
```json
{
  "order_status": "Delivered"
}
```

**Response:** `200 OK`
```json
{
  "message": "Order status updated",
  "detail": "Order #1 status: Delivered"
}
```

---

#### 9. Shopping List (Optional)

**Add to Shopping List:**
```http
POST /api/shopping-list
Authorization: Bearer <token>
```

**Request:**
```json
{
  "ingredient_id": 1,
  "quantity_to_buy": 1000
}
```

**View Shopping List:**
```http
GET /api/shopping-list
Authorization: Bearer <token>
```

**Remove from Shopping List:**
```http
DELETE /api/shopping-list/{ingredient_id}
Authorization: Bearer <token>
```

**Note:** Shopping list is for manual tracking. Most workflows go directly from availability check → recommendations → order.

---

### Recipe APIs

#### 1. Create Recipe

```http
POST /api/recipes
Authorization: Bearer <token>
```

**Request:**
```json
{
  "recipe_name": "Scrambled Eggs",
  "description": "Quick and easy breakfast",
  "cooking_time": 10,
  "requirements": [
    {
      "ingredient_id": 2,
      "quantity_needed": 4
    },
    {
      "ingredient_id": 1,
      "quantity_needed": 50
    }
  ],
  "steps": [
    {
      "step_number": 1,
      "description": "Crack eggs into bowl"
    },
    {
      "step_number": 2,
      "description": "Add milk and whisk"
    },
    {
      "step_number": 3,
      "description": "Cook in pan until done"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "recipe_id": 1,
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "owner_name": "alice",
  "recipe_name": "Scrambled Eggs",
  "description": "Quick and easy breakfast",
  "cooking_time": 10,
  "status": "Published",
  "created_at": "2025-12-07T10:00:00",
  "updated_at": "2025-12-07T10:00:00",
  "avg_rating": null,
  "total_reviews": 0
}
```

---

#### 2. List Recipes

```http
GET /api/recipes?search=scrambled
```

**Query Parameters:**
- `search` (optional): Filter by recipe name

**Response:** `200 OK`
```json
[
  {
    "recipe_id": 1,
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "owner_name": "alice",
    "recipe_name": "Scrambled Eggs",
    "description": "Quick and easy breakfast",
    "cooking_time": 10,
    "status": "Published",
    "created_at": "2025-12-07T10:00:00",
    "updated_at": "2025-12-07T10:00:00",
    "avg_rating": 4.5,
    "total_reviews": 10
  }
]
```

---

#### 3. Get Recipe Details

```http
GET /api/recipes/{recipe_id}
```

**Response:** `200 OK`
```json
{
  "recipe_id": 1,
  "owner_name": "alice",
  "recipe_name": "Scrambled Eggs",
  "description": "Quick and easy breakfast",
  "cooking_time": 10,
  "status": "Published",
  "created_at": "2025-12-07T10:00:00",
  "requirements": [
    {
      "ingredient_id": 2,
      "ingredient_name": "Eggs",
      "standard_unit": "unit",
      "quantity_needed": 4
    },
    {
      "ingredient_id": 1,
      "ingredient_name": "Milk",
      "standard_unit": "ml",
      "quantity_needed": 50
    }
  ],
  "steps": [
    {
      "step_number": 1,
      "description": "Crack eggs into bowl"
    },
    {
      "step_number": 2,
      "description": "Add milk and whisk"
    },
    {
      "step_number": 3,
      "description": "Cook in pan until done"
    }
  ],
  "avg_rating": 4.5,
  "total_reviews": 10
}
```

---

#### 4. Cook Recipe (FIFO Consumption)

```http
POST /api/recipes/{recipe_id}/cook
Authorization: Bearer <token>
```

**Request:**
```json
{
  "fridge_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response:** `200 OK`
```json
{
  "recipe_name": "Scrambled Eggs",
  "ingredients_consumed": [
    {
      "ingredient": "Eggs",
      "quantity": "4",
      "unit": "unit",
      "items_consumed": 1
    },
    {
      "ingredient": "Milk",
      "quantity": "50",
      "unit": "ml",
      "items_consumed": 2
    }
  ],
  "success": true,
  "message": "Successfully cooked 'Scrambled Eggs' using FIFO ingredient consumption"
}
```

**How It Works:**
1. Checks all ingredients available
2. Consumes each using FIFO (earliest expiry first)
3. Returns detailed consumption report

---

#### 5. Review Recipe

```http
POST /api/recipes/{recipe_id}/reviews
Authorization: Bearer <token>
```

**Request:**
```json
{
  "rating": 5,
  "comment": "Delicious and easy to make!"
}
```

**Response:** `201 Created`
```json
{
  "message": "Review submitted successfully",
  "detail": "Rated 5 stars"
}
```

---

#### 6. Get Recipe Reviews

```http
GET /api/recipes/{recipe_id}/reviews
```

**Response:** `200 OK`
```json
[
  {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_name": "alice",
    "recipe_id": 1,
    "rating": 5,
    "comment": "Delicious and easy to make!",
    "review_date": "2025-12-07T11:00:00"
  }
]
```

---

### Meal Planning APIs

#### 1. Create Meal Plan

```http
POST /api/meal-plans
Authorization: Bearer <token>
```

**Request:**
```json
{
  "recipe_id": 1,
  "planned_date": "2025-12-15"
}
```

**Response:** `201 Created`
```json
{
  "message": "Meal scheduled successfully",
  "detail": "Plan ID: 1"
}
```

**Initial Status:** `"Planned"`

---

#### 2. View Meal Plans

```http
GET /api/meal-plans?start_date=2025-12-01&end_date=2025-12-31
Authorization: Bearer <token>
```

**Query Parameters (both optional):**
- `start_date`: Filter from date (YYYY-MM-DD)
- `end_date`: Filter to date (YYYY-MM-DD)

**Response:** `200 OK`
```json
[
  {
    "plan_id": 1,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "recipe_id": 1,
    "recipe_name": "Scrambled Eggs",
    "planned_date": "2025-12-08",
    "status": "Ready"
  },
  {
    "plan_id": 2,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "recipe_id": 2,
    "recipe_name": "Pasta Carbonara",
    "planned_date": "2025-12-15",
    "status": "Insufficient"
  },
  {
    "plan_id": 3,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "recipe_id": 3,
    "recipe_name": "Stir Fry",
    "planned_date": "2025-12-25",
    "status": "Planned"
  }
]
```

**Status Values:**
- `Planned`: >14 days away (not checked yet)
- `Ready`: ≤14 days, all ingredients available
- `Insufficient`: ≤14 days, missing ingredients
- `Finished`: Recipe has been cooked
- `Canceled`: User canceled the plan

**Note:** Status is auto-updated by backend when inventory changes or periodically.

---

## Workflows

### Workflow 1: Basic Setup

```
1. Register → POST /api/auth/register
2. Login → POST /api/auth/login (save token!)
3. Create Fridge → POST /api/fridges
4. Create Ingredients → POST /api/ingredients (milk, eggs, etc.)
5. Add Items to Fridge → POST /api/fridges/{fridge_id}/items
```

---

### Workflow 2: Create and Cook Recipe

```
1. Create Recipe → POST /api/recipes
2. View Inventory → GET /api/fridges/{fridge_id}/items
3. Cook Recipe → POST /api/recipes/{recipe_id}/cook
   (automatically consumes ingredients using FIFO)
4. Review Recipe → POST /api/recipes/{recipe_id}/reviews
```

---

### Workflow 3: Meal Planning with Procurement ⭐ MAIN WORKFLOW

```javascript
// 1. User schedules meal plan
const mealPlan = await POST('/api/meal-plans', {
  recipe_id: 1,
  planned_date: '2025-12-15'
});

// 2. Check availability
const availability = await GET(
  '/api/availability/check?' +
  'recipe_id=1&' +
  'fridge_id=123...&' +
  'needed_by=2025-12-15'
);

if (!availability.all_available) {
  // 3. For each missing ingredient, get recommendations
  for (const ingredient of availability.missing_ingredients) {
    const recommendations = await GET(
      '/api/products/recommendations?' +
      `ingredient_id=${ingredient.ingredient_id}&` +
      `quantity_needed=${ingredient.shortage}&` +
      `needed_by=${ingredient.needed_by}`
    );

    // 4. Show options to user (sorted by price)
    displayProducts(recommendations.products);

    // User selects product (or frontend auto-selects first one - cheapest)
    const selectedSKU = recommendations.products[0].external_sku;

    // 5. Create order
    await POST('/api/orders', {
      fridge_id: '123...',
      items: [
        {
          external_sku: selectedSKU,
          quantity: 1
        }
      ]
    });
  }
}

// 6. When order arrives, add to fridge
await POST('/api/fridges/{fridge_id}/items', {
  ingredient_id: ingredient.ingredient_id,
  quantity: 1000,
  expiry_date: '2025-12-20'
});

// 7. Meal plan status auto-updates to "Ready"

// 8. On Dec 15, cook the meal
await POST('/api/recipes/1/cook', {
  fridge_id: '123...'
});
// Meal plan status auto-updates to "Finished"
```

---

### Workflow 4: Shared Fridge with Roommate

```
Alice (Owner):
1. POST /api/fridges (create fridge)
2. POST /api/fridges/{fridge_id}/members (invite Bob with role="Member")

Bob (Member):
3. GET /api/fridges (sees fridge with role="Member")
4. POST /api/fridges/{fridge_id}/items (can add items)
5. POST /api/fridges/{fridge_id}/consume (can consume items)
6. POST /api/fridges/{fridge_id}/members ❌ DENIED (only Owners can manage members)

Both:
- Create meal plans
- Cook recipes
- Both meal plans considered in availability check
```

---

## Common Patterns

### Pattern 1: Authorization Header

**Every protected endpoint needs:**
```javascript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

---

### Pattern 2: Date Format

**All dates use ISO 8601:**
```
Date: "2025-12-15"
DateTime: "2025-12-15T10:30:00"
```

---

### Pattern 3: UUIDs vs IDs

**UUIDs (string):**
- `user_id`
- `fridge_id`

**Integer IDs:**
- `ingredient_id`
- `recipe_id`
- `partner_id`
- `order_id`
- `plan_id`

---

### Pattern 4: FIFO Consumption

**Whenever consuming ingredients:**
- System **automatically** uses earliest expiring items first
- No manual batch selection needed
- Transparent to frontend

---

### Pattern 5: Error Responses

**All errors follow this format:**
```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: No/invalid token
- `403 Forbidden`: No permission (e.g., Member trying to add members)
- `404 Not Found`: Resource doesn't exist
- `500 Internal Server Error`: Server error

---

## Error Handling

### Example Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```
**Solution:** Include valid token in `Authorization` header.

---

**403 Forbidden:**
```json
{
  "detail": "Only owners can manage members"
}
```
**Solution:** User needs Owner role for this operation.

---

**404 Not Found (Availability Check):**
```json
{
  "detail": "No products can arrive by 2025-12-15 for Milk"
}
```
**Solution:** Adjust needed_by date or find alternative suppliers.

---

**400 Bad Request (Order):**
```json
{
  "detail": "All products in an order must be from the same partner"
}
```
**Solution:** Split into multiple orders (one per partner).

---

**400 Bad Request (Cooking):**
```json
{
  "detail": "Insufficient ingredients: Milk: need 500 ml, have 200 ml"
}
```
**Solution:** Order more ingredients before cooking.

---

## Health Checks

**Overall Health:**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "databases": {
    "postgres": "connected",
    "mongodb": "connected"
  },
  "errors": null
}
```

---

## Tips for Frontend Developers

### 1. Token Management
```javascript
// Store token after login
localStorage.setItem('token', response.access_token);

// Use in all requests
const token = localStorage.getItem('token');
fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Clear on logout
localStorage.removeItem('token');
```

---

### 2. Automatic Workflow
```javascript
// Recommended: Auto-select cheapest product
async function orderMissingIngredients(availability) {
  for (const ingredient of availability.missing_ingredients) {
    const recs = await getRecommendations(
      ingredient.ingredient_id,
      ingredient.shortage,
      ingredient.needed_by
    );

    // First product is cheapest!
    const cheapest = recs.products[0];

    await createOrder({
      fridge_id: currentFridgeId,
      items: [
        {
          external_sku: cheapest.external_sku,
          quantity: Math.ceil(ingredient.shortage / parseFloat(cheapest.selling_unit))
        }
      ]
    });
  }
}
```

---

### 3. Date Calculations
```javascript
// Format date for API
const formatDate = (date) => date.toISOString().split('T')[0];

// Parse date from API
const parseDate = (dateStr) => new Date(dateStr);

// Check if product arrives in time
const arrivesInTime = (product, needed_by) => {
  return new Date(product.expected_arrival) <= new Date(needed_by);
};
```

---

### 4. Status Display
```javascript
const statusColors = {
  'Planned': 'gray',
  'Ready': 'green',
  'Insufficient': 'red',
  'Finished': 'blue',
  'Canceled': 'gray'
};

const statusIcons = {
  'Planned': '📅',
  'Ready': '✅',
  'Insufficient': '⚠️',
  'Finished': '✓',
  'Canceled': '✗'
};
```

---

### 5. FIFO Visualization
```javascript
// Show which batches will be used
function visualizeFIFO(items, consumeQty) {
  let remaining = consumeQty;
  const used = [];

  // Items already sorted by expiry_date
  for (const item of items) {
    if (remaining <= 0) break;

    const used_from_batch = Math.min(item.quantity, remaining);
    used.push({
      item_id: item.item_id,
      expiry_date: item.expiry_date,
      used: used_from_batch,
      total: item.quantity
    });
    remaining -= used_from_batch;
  }

  return used;
}
```

---

## Summary

### Key Features
✅ **Shared Fridges** - Multiple users with roles
✅ **FIFO Consumption** - Automatic earliest-expiry-first
✅ **Timeline Simulation** - Predicts shortages considering future events
✅ **Frontend-Driven Ordering** - User picks products, backend validates
✅ **Meal Plan Status** - Auto-updated based on availability
✅ **Price Snapshots** - Orders save prices (immutable)

### Quick Start
1. Register & Login → Get token
2. Create Fridge → Get fridge_id
3. Add Ingredients → Get ingredient_id
4. Create Products → Link partners to ingredients
5. Create Meal Plan → Get availability check → Order missing ingredients
6. Cook & Enjoy!

---

**Questions?** Check the interactive API docs at: `http://localhost:8000/docs`
