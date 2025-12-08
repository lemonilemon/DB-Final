# Database Foreign Key Cascade Rules

**Last Updated**: December 9, 2025

This document summarizes all foreign key relationships and their cascade behavior when parent records are deleted or updated.

## Cascade Rule Legend

- **CASCADE**: Automatically delete/update child records when parent is deleted/updated
- **RESTRICT**: Prevent deletion/update of parent if child records exist
- **SET NULL**: Set foreign key to NULL when parent is deleted (requires nullable column)

---

## Foreign Key Relationships by Table

### external_product
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| partner_id | partner.partner_id | CASCADE | **RESTRICT** | Cannot delete partner with products |
| ingredient_id | ingredient.ingredient_id | CASCADE | **RESTRICT** | Cannot delete ingredient with products |

**Business Logic**: Products are inventory records that must be explicitly removed before deleting partners or ingredients.

---

### fridge_access
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| fridge_id | fridge.fridge_id | CASCADE | **CASCADE** | Access removed when fridge deleted |
| user_id | user.user_id | CASCADE | **CASCADE** | Access removed when user deleted |

**Business Logic**: Access permissions are tied to fridge/user existence and should be automatically cleaned up.

---

### fridge_item
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| fridge_id | fridge.fridge_id | CASCADE | **CASCADE** | Items deleted when fridge deleted |
| ingredient_id | ingredient.ingredient_id | CASCADE | **RESTRICT** | Cannot delete ingredient with inventory |

**Business Logic**: Fridge contents are deleted with the fridge. Ingredients are master data protected from deletion.

---

### meal_plan
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| fridge_id | fridge.fridge_id | CASCADE | **CASCADE** | Meal plans deleted when fridge deleted |
| recipe_id | recipe.recipe_id | CASCADE | **CASCADE** | Meal plans deleted when recipe deleted |
| user_id | user.user_id | CASCADE | **CASCADE** | Meal plans deleted when user deleted |

**Business Logic**: Meal plans are ephemeral scheduling data tied to specific fridges, recipes, and users.

---

### order_item
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| order_id | store_order.order_id | CASCADE | **CASCADE** | Line items deleted when order deleted |
| (partner_id, external_sku) | external_product | CASCADE | **RESTRICT** | Cannot delete product with orders |

**Business Logic**: Order items are part of the order. Products cannot be deleted if they have order history.

**Note**: Composite foreign key on (partner_id, external_sku) ensures referential integrity with the composite primary key.

---

### recipe
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| owner_id | user.user_id | CASCADE | **RESTRICT** | Cannot delete user with recipes |

**Business Logic**: Recipes are user content that must be explicitly deleted or reassigned before user deletion.

---

### recipe_requirement
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| recipe_id | recipe.recipe_id | CASCADE | **CASCADE** | Requirements deleted when recipe deleted |
| ingredient_id | ingredient.ingredient_id | CASCADE | **RESTRICT** | Cannot delete ingredient used in recipes |

**Business Logic**: Recipe requirements are part of the recipe definition.

---

### recipe_review
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| recipe_id | recipe.recipe_id | CASCADE | **CASCADE** | Reviews deleted when recipe deleted |
| user_id | user.user_id | CASCADE | **CASCADE** | Reviews deleted when user deleted |

**Business Logic**: Reviews are tied to both recipe and user existence.

---

### recipe_step
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| recipe_id | recipe.recipe_id | CASCADE | **CASCADE** | Steps deleted when recipe deleted |

**Business Logic**: Steps are part of the recipe definition.

---

### shopping_list_item
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| user_id | user.user_id | CASCADE | **CASCADE** | Shopping list deleted when user deleted |
| ingredient_id | ingredient.ingredient_id | CASCADE | **RESTRICT** | Cannot delete ingredient in shopping lists |

**Business Logic**: Shopping lists are user-specific carts that should be cleaned up with user deletion.

---

### store_order ⚠️ SPECIAL CASE
| Column | References | ON UPDATE | ON DELETE | Notes |
|--------|-----------|-----------|-----------|-------|
| user_id | user.user_id | CASCADE | **RESTRICT** | Cannot delete user with order history |
| partner_id | partner.partner_id | CASCADE | **RESTRICT** | Cannot delete partner with order history |
| fridge_id | fridge.fridge_id | CASCADE | **SET NULL** | Order preserved, fridge link removed |

**Business Logic**:
- Orders are **financial records** that must be preserved for accounting/audit purposes
- Users and partners cannot be deleted if they have order history (use soft delete pattern if needed)
- **fridge_id is NULLABLE**: When a fridge is deleted, orders are kept but the fridge association is set to NULL
- This allows fridge deletion while preserving complete order history

**Important**: This is the ONLY table where fridge deletion uses SET NULL instead of CASCADE or RESTRICT.

---

## Summary of Cascade Patterns

### Master Data (Protected with RESTRICT)
These entities cannot be deleted if referenced:
- **ingredient**: Protected in external_product, fridge_item, recipe_requirement, shopping_list_item
- **partner**: Protected in external_product, store_order
- **user**: Protected in recipe (owner), store_order

### Transactional Data (Preserved with RESTRICT)
- **store_order**: Financial records cannot be cascaded
- **external_product**: Historical product records protected

### Ephemeral/Derived Data (Cleaned with CASCADE)
- **fridge** → fridge_access, fridge_item, meal_plan (CASCADE)
- **fridge** → store_order (SET NULL - special case)
- **recipe** → recipe_requirement, recipe_step, recipe_review, meal_plan (CASCADE)
- **user** → fridge_access, meal_plan, recipe_review, shopping_list_item (CASCADE)

---

## Deletion Workflow Examples

### ✅ Safe: Delete a Fridge
```sql
DELETE FROM fridge WHERE fridge_id = '...';
```
**Result**:
- ✓ fridge_access records CASCADE deleted
- ✓ fridge_item records CASCADE deleted
- ✓ meal_plan records CASCADE deleted
- ✓ store_order.fridge_id SET to NULL (orders preserved)

### ❌ Blocked: Delete a Partner with Orders
```sql
DELETE FROM partner WHERE partner_id = 1;
-- ERROR: Cannot delete partner with order history (RESTRICT)
```
**Solution**: Orders are financial records. Do not delete partners, or use soft delete pattern.

### ❌ Blocked: Delete an Ingredient in Use
```sql
DELETE FROM ingredient WHERE ingredient_id = 5;
-- ERROR: Ingredient referenced in external_product, fridge_item, or recipes (RESTRICT)
```
**Solution**: Remove all references before deleting master data.

---

## Database Integrity Guarantees

1. **Financial Audit Trail**: Store orders and order items are always preserved
2. **Master Data Protection**: Core entities (ingredients, partners) cannot be accidentally deleted
3. **Automatic Cleanup**: Temporary data (carts, access permissions) automatically cleaned up
4. **Referential Integrity**: All foreign keys properly enforced with appropriate cascade rules

---

**⚠️ Important for Frontend Development**:
- When deleting a fridge, inform users that order history will be preserved but fridge association removed
- When attempting to delete partners/ingredients, check for references and guide user to cleanup
- Store orders are immutable records - provide "cancel" functionality instead of deletion
