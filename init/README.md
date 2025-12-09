# Database Initialization Scripts

This directory contains database schema initialization scripts for the NEW Fridge system.

## Directory Structure

```
init/
├── postgres/
│   └── 01_schema.sql          # PostgreSQL schema (15 tables)
├── mongo/
│   └── 01_schema.js           # MongoDB schema (3 collections)
└── README.md                  # This file
```

## PostgreSQL Schema (`postgres/01_schema.sql`)

### Tables (15 total)

#### User Management
- **user** - User accounts with authentication (UUID PK, bcrypt passwords)
- **fridge_access** - Multi-tenant fridge permissions (Owner/Member roles)

#### Inventory Management
- **fridge** - Shared fridges
- **ingredient** - Master ingredient catalog with standard units (g, ml, pcs)
- **fridge_item** - FIFO inventory tracking with expiry dates

#### Recipe System
- **recipe** - User-created recipes
- **recipe_requirement** - Recipe ingredients (composite PK)
- **recipe_step** - Cooking instructions (composite PK)
- **recipe_review** - User ratings and comments

#### Meal Planning
- **meal_plan** - Scheduled recipes with auto-status evaluation
  - Status: Planned, Ready, Insufficient, Finished, Cancelled
  - Auto-updated on inventory/order changes

#### Procurement
- **partner** - Supplier information with shipping times
- **external_product** - Products with unit conversion (composite PK)
- **shopping_list_item** - User cart with optional deadlines
- **store_order** - Purchase orders (split by partner)
- **order_item** - Order line items with price snapshots

### Key Features

#### Composite Primary Keys
- `external_product`: (partner_id, external_sku)
- `order_item`: (order_id, external_sku)
- `recipe_requirement`: (recipe_id, ingredient_id)
- `recipe_step`: (recipe_id, step_number)
- `recipe_review`: (user_id, recipe_id)
- `shopping_list_item`: (user_id, ingredient_id)
- `fridge_access`: (user_id, fridge_id)

#### Unit Conversion System
```sql
-- Example: external_product
product_name: "Milk 1L Bottle"
selling_unit: "1L Bottle"          -- Descriptive
unit_quantity: 1000                 -- 1000ml per bottle
standard_unit: "ml"                 -- From ingredient table
```

Conversion formula: `packages_needed = CEIL(quantity_needed / unit_quantity)`

#### CASCADE Rules
- `ON DELETE CASCADE`: Child records deleted automatically
  - user → fridge_access, shopping_list_item
  - fridge → fridge_access, fridge_item, meal_plan
  - recipe → recipe_requirement, recipe_step, recipe_review, meal_plan
  - store_order → order_item

- `ON DELETE RESTRICT`: Prevents deletion if references exist
  - ingredient (widely referenced)
  - partner (has products/orders)
  - user (recipe owner)

- `ON DELETE SET NULL`: Preserves order history
  - fridge_id in store_order (if fridge deleted)

## MongoDB Schema (`mongo/01_schema.js`)

### Collections (3 total)

#### 1. activity_logs
User behavior tracking for analytics

**Fields:**
- `user_id` (string, UUID)
- `action_type` (string) - login, search_recipe, view_recipe, cook_recipe, create_order, view_fridge
- `resource_type` (string) - recipe, ingredient, order, fridge
- `resource_id` (string)
- `timestamp` (date)
- `metadata` (object) - Additional context

**Indexes:**
- `(user_id, timestamp)`
- `(action_type, timestamp)`
- `(resource_type, resource_id)`

**Use Cases:**
- User activity dashboards
- Recipe popularity tracking
- Behavior analysis

#### 2. search_queries
Search analytics and trends

**Fields:**
- `user_id` (string, UUID)
- `query_type` (string) - recipe, ingredient
- `query_text` (string)
- `results_count` (int)
- `timestamp` (date)
- `filters` (object)

**Indexes:**
- `(user_id, timestamp)`
- `(query_type, query_text)`
- `query_text` (text index for full-text search)

**Use Cases:**
- Popular search terms
- Search trends over time
- Query optimization

#### 3. api_usage
API performance monitoring

**Fields:**
- `endpoint` (string)
- `method` (string) - GET, POST, PUT, DELETE
- `user_id` (string, UUID)
- `status_code` (int)
- `response_time_ms` (double)
- `timestamp` (date)
- `ip_address` (string)
- `user_agent` (string)

**Indexes:**
- `(endpoint, method, timestamp)`
- `(user_id, timestamp)`
- `(status_code, timestamp)`

**Use Cases:**
- Performance monitoring
- Error tracking
- Usage analytics

## Usage

### PostgreSQL Initialization

The schema is automatically created by SQLModel in the application. This file serves as documentation and can be used for manual initialization:

```bash
# Manual initialization (if needed)
docker compose exec postgres psql -U postgres -d postgres -f /init/postgres/01_schema.sql
```

### MongoDB Initialization

MongoDB collections are created on-demand by the application. For manual initialization:

```bash
# Run initialization script
docker compose exec mongodb mongosh admin -u root -p password --file /init/mongo/01_schema.js
```

## Schema Modifications

### Adding a New Table (PostgreSQL)

1. Create model in `backend/models/`
2. Add to `models/__init__.py`
3. Update this schema file for documentation
4. Restart backend (SQLModel auto-creates tables)

### Adding a New Collection (MongoDB)

1. Define schema in `backend/schemas/behavior.py`
2. Add logging in `backend/services/behavior_service.py`
3. Update `mongo/01_schema.js` with indexes
4. Run initialization script or let app create on-demand

## Important Notes

### PostgreSQL
- All tables use proper foreign key constraints
- Indexes created for common query patterns
- Enum type for user roles (User, Admin)
- Composite primary keys where appropriate
- Check constraints for data validation

### MongoDB
- Schema validation enabled (moderate level)
- Compound indexes for query performance
- TTL indexes can be added for log rotation
- JSON Schema validators ensure data quality

## Data Generation

See `backend/generate_data.py` for PostgreSQL test data (86K+ records).
See `backend/generate_behavioral_data.py` for MongoDB test data (1K+ logs).

## Maintenance

### Clean Old Logs (MongoDB)

```javascript
// Remove logs older than 90 days
const cutoff = new Date(Date.now() - 90*24*60*60*1000);
db.activity_logs.deleteMany({ timestamp: { $lt: cutoff } });
db.search_queries.deleteMany({ timestamp: { $lt: cutoff } });
db.api_usage.deleteMany({ timestamp: { $lt: cutoff } });
```

Or use the API endpoint:
```bash
POST /api/analytics/admin/cleanup-logs?days_to_keep=90
```

### Backup & Restore

```bash
# PostgreSQL backup
bash backend/scripts/backup_database.sh

# Restore backup
bash backend/scripts/restore_database.sh backend/backups/db_backup_TIMESTAMP.sql.gz
```

## Schema Version

**Current Version:** 1.0.0
**Last Updated:** December 10, 2025
**Total Tables:** 15 (PostgreSQL) + 3 (MongoDB)
**Total Records:** ~86,000 (PostgreSQL) + ~1,000 (MongoDB)
