# NEW Fridge - Smart Inventory Management System

A full-stack application for managing fridge inventory, recipes, meal planning, and procurement with behavioral analytics.

## Tech Stack

- **Backend:** FastAPI (Python 3.13)
- **Primary Database:** PostgreSQL (with UUID, ENUM types)
- **Analytics Database:** MongoDB
- **Containerization:** Docker & Docker Compose

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Ports 8000 (API), 5432 (PostgreSQL), 27017 (MongoDB) available

### Start All Services
```bash
docker compose up -d
```

### Check Health
```bash
curl http://localhost:8000/health
```

### Stop Services
```bash
docker compose down
```

---

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── database.py             # PostgreSQL connection
├── mongodb.py              # MongoDB connection
├── core/
│   ├── config.py          # Environment configuration
│   ├── security.py        # JWT & password hashing
│   └── dependencies.py    # Auth & authorization
├── models/                # SQLModel database models
│   ├── user.py
│   ├── fridge.py
│   ├── inventory.py
│   ├── recipe.py
│   └── procurement.py
├── routers/               # API endpoints
│   ├── auth.py           # Registration & login
│   ├── fridge.py         # Fridge management
│   ├── inventory.py      # Ingredient & items
│   ├── recipe.py         # Recipe & meal plans
│   ├── procurement.py    # Shopping & orders
│   ├── analytics.py      # Behavior analytics
│   └── admin_users.py    # Admin user management
├── services/             # Business logic
│   ├── auth_service.py
│   ├── fridge_service.py
│   ├── recipe_service.py
│   ├── procurement_service.py
│   └── behavior_service.py
├── schemas/              # Pydantic request/response models
├── middleware/           # Request/response middleware
└── migrations/           # SQL migration scripts
```

---

## Database Schema

### PostgreSQL Tables (15 total)

**User & Authentication:**
- `user` - User accounts with single role (User/Admin)

**Fridge Management:**
- `fridge` - Shared refrigerators
- `fridge_access` - User permissions (Owner/Member)
- `fridge_item` - Inventory items with expiry dates

**Inventory:**
- `ingredient` - Master ingredient catalog

**Recipe System:**
- `recipe` - User-created recipes
- `recipe_requirement` - Ingredients per recipe
- `recipe_step` - Cooking instructions
- `recipe_review` - User ratings
- `meal_plan` - Scheduled meals

**Procurement:**
- `partner` - External suppliers
- `external_product` - Products from partners
- `shopping_list_item` - User shopping lists
- `store_order` - Orders placed
- `order_item` - Order line items

See `DATABASE_SCHEMA.md` for complete schema details.

### MongoDB Collections

- `user_behavior` - User actions (login, view, cook, etc.)
- `api_usage` - API endpoint performance tracking
- `search_queries` - Search behavior analytics

---

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication Endpoints

**Register User**
```bash
POST /api/auth/register
Content-Type: application/json

{
  "user_name": "johndoe",
  "email": "john@example.com",
  "password": "password123"
}
```

**Login**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "user_name": "johndoe",
  "password": "password123"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "uuid-here",
  "user_name": "johndoe",
  "role": "User"
}
```

**Get Current User**
```bash
GET /api/me
Authorization: Bearer <token>
```

### Protected Endpoints

All endpoints except `/api/auth/*` require authentication:
```bash
Authorization: Bearer <your_jwt_token>
```

### Main Features

**Fridge Management:** `/api/fridges/*`
- Create, list, update fridges
- Manage user access (Owner/Member)
- View fridge inventory

**Inventory:** `/api/ingredients/*`, `/api/inventory/*`
- Browse ingredient catalog
- Add/remove items from fridge
- Track expiry dates

**Recipes & Meal Planning:** `/api/recipes/*`, `/api/meal-plans/*`
- Create and share recipes
- Check ingredient availability
- Cook recipes (auto-consumes ingredients FIFO)
- Schedule meal plans

**Procurement:** `/api/partners/*`, `/api/products/*`, `/api/shopping-list/*`, `/api/orders/*`
- Browse partner products
- Manage shopping lists
- Place orders
- Track order status

**Analytics:** `/api/analytics/*`
- User activity statistics
- Recipe popularity
- API performance metrics

**Admin (Admin role required):** `/api/admin/*`
- Manage all users
- Update user status
- Grant/revoke admin role
- Manage all orders

See `API_DOCUMENTATION.md` for complete endpoint reference.

---

## Key Features

### 1. Role-Based Access Control (RBAC)
- **User:** Standard access (own data only)
- **Admin:** Full system access
- Implemented via PostgreSQL ENUM type
- Single role per user

### 2. Multi-User Fridge Sharing
- Multiple users can share a fridge
- Owner and Member roles
- Access control per fridge

### 3. FIFO Inventory Management
- Tracks ingredient batches with entry/expiry dates
- Auto-consumes oldest items first when cooking

### 4. Recipe Availability Check
- Checks fridge inventory before cooking
- Intelligent timeline simulation
- Considers expiry dates and meal plan schedule

### 5. Behavioral Analytics
- MongoDB tracks all user actions
- API performance monitoring
- Search query analysis
- Automatic behavior logging via middleware

### 6. CORS Support
Configured for common frontend frameworks:
- React (port 3000)
- Vite (port 5173)
- Vue (port 8080)
- Angular (port 4200)

---

## Environment Variables

Create `.env` file or set in `docker-compose.yml`:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=postgres
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=password

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS (optional, for production)
CORS_ORIGINS=https://yourdomain.com
```

---

## Common Tasks

### Create Admin User

**Option 1: Via Database**
```bash
docker compose exec postgres psql -U postgres -d postgres -c \
  "UPDATE \"user\" SET role = 'Admin' WHERE user_name = 'your_username';"
```

**Option 2: Via API (requires existing admin)**
```bash
curl -X POST http://localhost:8000/api/admin/users/{user_id}/roles/Admin \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### View Database Schema
```bash
docker compose exec postgres psql -U postgres -d postgres -c "\dt"
```

### View Logs
```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Database only
docker compose logs -f postgres
```

### Database Migrations
```bash
# Run migration script
docker compose exec postgres psql -U postgres -d postgres \
  < backend/migrations/migrate_to_single_role.sql
```

---

## Development

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Run Backend Locally (without Docker)
```bash
# Set environment variables
export POSTGRES_HOST=localhost
export MONGO_HOST=localhost

# Run
uvicorn main:app --reload --port 8000
```

### Code Structure Guidelines
- **Models:** SQLModel classes (in `models/`)
- **Schemas:** Pydantic models for API (in `schemas/`)
- **Services:** Business logic (in `services/`)
- **Routers:** API endpoints (in `routers/`)
- **Dependencies:** Reusable dependencies (in `core/dependencies.py`)

---

## Testing Examples

### Register and Login Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"user_name":"testuser","email":"test@test.com","password":"test12345"}'

# 2. Login (get token)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_name":"testuser","password":"test12345"}' \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# 3. Access protected endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/me
```

### Create Fridge and Add Items
```bash
# Create fridge
curl -X POST http://localhost:8000/api/fridges \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"fridge_name":"My Fridge","description":"Home fridge"}'

# Add item to fridge
curl -X POST http://localhost:8000/api/inventory/{fridge_id}/items \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"ingredient_id":1,"quantity":500,"expiry_date":"2025-12-31"}'
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Stop the service and restart
docker compose down
docker compose up -d
```

### Database Connection Error
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

### CORS Errors
- Verify your frontend URL is in `allowed_origins` (in `main.py`)
- Default ports are already configured: 3000, 5173, 8080, 4200
- For custom port, add it to `allowed_origins` list

### Reset Database
```bash
# WARNING: This deletes all data
docker compose down -v
docker compose up -d
```

---

## Performance Optimization

1. **Database Indexes:** Already configured on frequently queried columns
2. **Connection Pooling:** AsyncPG with connection pooling enabled
3. **FIFO Queries:** Optimized with index on `entry_date`
4. **MongoDB Caching:** 15-minute cache for analytics queries
5. **JWT Tokens:** Validated in-memory (no DB query)

---

## Security Features

- **Password Hashing:** BCrypt with 12 rounds
- **JWT Authentication:** HS256 algorithm
- **Role-Based Access:** PostgreSQL ENUM enforced
- **SQL Injection Protection:** Parameterized queries via SQLAlchemy
- **CORS Protection:** Whitelist-based origin control
- **Input Validation:** Pydantic schema validation

---

## License

This is a student project for database course final project.

---

## Support

For issues or questions:
1. Check `API_DOCUMENTATION.md` for endpoint details
2. Check `DATABASE_SCHEMA.md` for schema reference
3. Review Docker Compose logs: `docker compose logs`

---

**Built with ❤️ using FastAPI, PostgreSQL, and MongoDB**
