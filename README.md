# NEW Fridge - Smart Inventory Management System

A smart inventory and procurement management system for shared fridges, featuring FIFO consumption tracking, automatic order splitting, and meal planning with availability checking.

**Database Systems Final Project** - Demonstrating advanced database concepts including composite indexes, FIFO algorithms, multi-tenancy, and query optimization.

---

## 📖 Introduction

### What is NEW Fridge?

NEW Fridge solves three common household problems:

1. **Food Waste** - Tracks expiry dates and automatically uses oldest items first (FIFO)
2. **Shared Fridge Chaos** - Multi-user access with role-based permissions (Owner/Member)
3. **Inefficient Shopping** - Automatically splits orders by supplier and finds cheapest products

### Key Features

- 🏠 **Multi-Tenant Fridges** - Share fridges with roommates/family
- 📦 **FIFO Inventory** - Consume oldest items first to prevent spoilage
- 🍳 **Meal Planning** - Check if you can cook a recipe with current + future inventory
- 🛒 **Smart Procurement** - Auto-split orders by partner, select cheapest products
- ⚡ **High Performance** - Optimized indexes for 50,000+ inventory items (4.6x speedup)

### Database Concepts Demonstrated

- **FIFO Composite Indexes** - `(fridge_id, ingredient_id, expiry_date ASC)` for sorted queries
- **Partial Indexes** - Index only active records (meal plans, pending orders)
- **Foreign Key Indexes** - All FKs manually indexed for JOIN performance
- **Multi-Tenancy** - Junction table pattern for shared resource access
- **Timeline Simulation** - Predictive inventory considering future meals + pending deliveries
- **Price Snapshotting** - Historical order prices (not current_price)

### Technology Stack

- **Backend**: FastAPI (Python 3.13), SQLModel (async SQLAlchemy 2.0)
- **Databases**: PostgreSQL 16 (transactional), MongoDB 7 (analytics)
- **Frontend**: React 18 + Vite
- **Infrastructure**: Docker Compose

### Performance Results

With optimized indexing strategy:
- **Fridge inventory lookup**: 16.46ms → 1.82ms (9x faster)
- **FIFO consumption query**: 7.93ms → 2.01ms (4x faster)
- **Expiry date search**: 37.33ms → 4.12ms (9x faster)
- **Overall query performance**: 84.25ms → 18.47ms (**4.6x faster**)

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - For backend services
- **Node.js 18+** and **npm** - For frontend development
- **8GB+ RAM** recommended
- **Ports available**: 8000, 5432, 27017, 5050, 8081, 5173

### 1. Start Backend Services

```bash
# Clone repository
git clone <repository-url>
cd final

# Copy environment variables
cp .env.example .env

# Start backend services (NOT frontend)
docker compose up -d

# Verify services are running
docker compose ps
```

**Expected services**:
- ✅ Backend API (port 8000)
- ✅ PostgreSQL (port 5432)
- ✅ MongoDB (port 27017)
- ✅ pgAdmin (port 5050)
- ✅ Mongo Express (port 8081)

### 1.5. Start Frontend (npm)

**Frontend runs locally with npm for better development experience:**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Expected output**:
```
  VITE v6.0.1  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

Frontend will be available at **http://localhost:5173** with hot reload enabled.

### 2. Initialize Database

**Apply schema**:
```bash
docker compose exec postgres psql -U postgres -d postgres \
    -f /docker-entrypoint-initdb.d/01_schema.sql
```

**Apply optimized indexes** (FIFO composite, FK indexes, partial indexes):
```bash
docker compose exec postgres psql -U postgres -d postgres \
    -f /docker-entrypoint-initdb.d/02_indexes.sql
```

**Verify indexes created**:
```bash
docker compose exec postgres psql -U postgres -d postgres \
    -c "SELECT indexname FROM pg_indexes WHERE tablename = 'fridge_item';"
```

Expected output should include `idx_fridge_item_fifo` (FIFO composite index).

### 3. Generate Test Data

```bash
docker compose exec backend python3 scripts/generate_data.py
docker compose exec backend python3 scripts/generate_behavioral_data.py
```

**Generates**:
- 500 users (1 admin + 499 regular)
- 300 fridges with shared access
- 150 ingredients
- 800 recipes
- 50,000 fridge items
- 20,000 meal plans
- 20 partners with 800 products

**Time**: ~30-60 seconds

### 4. Access Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **pgAdmin** | http://localhost:5050 | admin@example.com / password |
| **Mongo Express** | http://localhost:8081 | admin / password |

**Test Login**:
- Admin: `admin` / `admin`
- User: `user` / `user`

### 5. Test the System

**Option A: Use Frontend** (http://localhost:5173)
1. Login as admin
2. Navigate to "Fridges" → Select a fridge
3. View inventory items
4. Go to "Meal Plans" → Create a meal plan
5. If status is "Insufficient" → Click "Add to Cart"
6. Go to "Shopping List" → Click "Checkout All"
7. Return to "Meal Plans" → Status should update to "Ready"

**Option B: Use API** (http://localhost:8000/docs)
1. POST `/api/auth/login` → Get token
2. GET `/api/fridges` → Get your fridges
3. GET `/api/fridges/{fridge_id}/items` → View inventory
4. GET `/api/meal-plans` → View meal plans
5. POST `/api/orders/from-shopping-list` → Create orders

---

## 📊 Performance Testing

**Run benchmark tests**:
```bash
# General index performance (8 common queries)
docker compose exec backend python3 scripts/test_performance.py
```

**What it tests**:
- Fridge inventory lookups
- FIFO consumption queries
- Date range searches (expiry dates)
- Meal plan filtering
- Order history queries

---

## 🛠️ Common Commands

```bash
# View backend logs
docker compose logs -f backend

# Restart backend
docker compose restart backend

# Rebuild after code changes
docker compose up --build backend

# Access PostgreSQL shell
docker compose exec postgres psql -U postgres -d postgres

# Access MongoDB shell
docker compose exec mongodb mongosh admin -u root -p password

# Stop all services
docker compose down

# Wipe data and restart fresh
docker compose down
docker volume rm final_postgres_data final_mongo_data
docker compose up -d
```

---

## 📁 Project Structure

```
final/
├── backend/
│   ├── core/              # Config, security, utils
│   ├── models/            # SQLModel ORM models
│   ├── schemas/           # Pydantic request/response DTOs
│   ├── routers/           # API endpoint controllers
│   ├── services/          # Business logic layer
│   │   ├── procurement_service.py  # FIFO, timeline, orders
│   │   ├── fridge_service.py       # Inventory, access control
│   │   └── recipe_service.py       # Recipes, meal plans
│   ├── scripts/           # Utility scripts
│   │   ├── generate_data.py        # Test data generator
│   │   ├── test_performance.py     # Index performance tests
│   │   └── test_fifo_performance.py  # FIFO benchmark
│   ├── database.py        # Async database engine
│   └── main.py            # FastAPI application entry
├── frontend/
│   └── src/
│       ├── api/           # API client functions
│       ├── pages/         # React page components
│       └── components/    # Reusable components
├── init/
│   ├── postgres/
│   │   ├── 01_schema.sql  # Database schema
│   │   └── 02_indexes.sql # Optimized indexes ⭐
│   └── mongo/
│       └── 01_schema.js   # MongoDB collections
├── docker-compose.yml
└── README.md
```

---

## 🗄️ Key Database Features

### FIFO Composite Index

**Problem**: FIFO queries need to filter by fridge + ingredient AND sort by expiry date.

**Solution**:
```sql
CREATE INDEX idx_fridge_item_fifo
ON fridge_item (fridge_id, ingredient_id, expiry_date ASC);
```

**Benefit**: Database reads data already sorted from index (no in-memory sort).

**Performance**: 7.93ms → 2.01ms (4x faster)

### Partial Indexes

**Concept**: Index only frequently-queried rows.

**Example**:
```sql
-- Only index active meal plans (exclude finished/cancelled)
CREATE INDEX idx_meal_plan_active
ON meal_plan(user_id, planned_date)
WHERE status NOT IN ('Finished', 'Cancelled');
```

**Benefit**: 30-50% smaller index, faster scans, less write overhead.

### Foreign Key Indexes

**Problem**: PostgreSQL doesn't auto-create FK indexes.

**Solution**: Manually index all foreign keys:
```sql
CREATE INDEX idx_fridge_item_fridge_id ON fridge_item(fridge_id);
CREATE INDEX idx_fridge_item_ingredient_id ON fridge_item(ingredient_id);
CREATE INDEX idx_meal_plan_recipe_id ON meal_plan(recipe_id);
-- ... etc
```

**Benefit**: 9x faster JOIN queries.

---

## 🧪 Testing Scenarios

### 1. FIFO Consumption Test

**Setup**: Add 3 milk batches with different expiry dates.

**Expected**: When consuming 600ml, oldest batch is used first.

### 2. Order Splitting Test

**Setup**: Add items from 2 different partners to cart.

**Expected**: "Checkout All" creates 2 separate orders (one per partner).

### 3. Meal Plan Status Update

**Setup**: Create meal plan without ingredients (status: "Insufficient").

**Expected**: After ordering ingredients, status auto-updates to "Ready".

---

## 📖 Documentation

- **Full Schema**: See `init/postgres/01_schema.sql`
- **Index Strategy**: See `init/postgres/02_indexes.sql`
- **API Reference**: http://localhost:8000/docs (interactive Swagger UI)
- **Development Guide**: See `CLAUDE.md`
- **Schema Decisions**: See `SCHEMA_FINALIZED.md`

---

## 🐛 Troubleshooting

**Services won't start**:
```bash
docker compose up --build
```

**Database connection errors**:
```bash
docker compose logs postgres
docker compose restart postgres
```

**Port already in use**:
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Modify ports in docker-compose.yml if needed
```

**Can't login to frontend**:
- Make sure you ran `generate_data.py` to create admin user
- Or register a new user via API: POST `/api/auth/register`

---

## 📄 License

Educational project for Database Systems course.

---

**Database Systems Final Project - Fall 2025**
