# NEW Fridge - Smart Inventory Management System

A dockerized microservices application for smart fridge inventory management, procurement, and recipe tracking. Built with FastAPI, PostgreSQL, MongoDB, and ReactJS.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM recommended
- Ports available: 8000, 5432, 27017, 5050, 8081

### 1. Start the Application

```bash
# Clone the repository (if needed)
cd /path/to/DB/final

# Start all services
docker compose up -d

# Check services are running
docker compose ps
```

**Services will start on:**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL (pgAdmin): http://localhost:5050
- MongoDB (Mongo Express): http://localhost:8081

### 2. Option A: Load Sample Data from Backup

We provide pre-generated sample data (500 users, 200 fridges, 15 recipes, 5,768 orders):

```bash
# Load the latest backup
gunzip -c backend/backups/db_backup_20251209_001634.sql.gz | \
  docker compose exec -T postgres psql -U postgres -d postgres

# Verify data loaded
docker compose exec postgres psql -U postgres -d postgres -c \
  "SELECT 'users' as table, COUNT(*) FROM \"user\"
   UNION ALL SELECT 'fridges', COUNT(*) FROM fridge
   UNION ALL SELECT 'recipes', COUNT(*) FROM recipe;"
```

**Expected output:**
```
  table  | count
---------+-------
 users   |   500
 fridges |   200
 recipes |    15
```

### 3. Option B: Generate Fresh Data

```bash
# Clear existing data (if any)
docker compose exec backend python scripts/clean_data.py

# Generate new sample data
docker compose exec backend python generate_data.py
```

### 4. Access Web Interfaces

**API Documentation (Swagger UI):**
- URL: http://localhost:8000/docs
- Interactive API testing
- No authentication required for public endpoints

**PostgreSQL Admin (pgAdmin):**
- URL: http://localhost:5050
- Email: `admin@example.com`
- Password: `password`
- Add server: Host=`postgres`, Port=`5432`, User=`postgres`, Password=`password`

**MongoDB Admin (Mongo Express):**
- URL: http://localhost:8081
- Username: `admin`
- Password: `password`

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/

# List all recipes
curl http://localhost:8000/api/recipes

# Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"user_name":"testuser","password":"password123","email":"test@example.com"}'
```

## Project Structure

```
.
├── backend/
│   ├── models/          # SQLModel database models
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── schemas/         # Request/response DTOs
│   ├── core/            # Config and security
│   ├── scripts/         # Utility scripts
│   └── backups/         # Database backups
├── init/
│   ├── postgres/        # PostgreSQL init scripts
│   └── mongo/           # MongoDB init scripts
├── frontend/            # React frontend (in development)
└── docker-compose.yml   # Services orchestration
```

## Key Features

- **Multi-Fridge Management**: Share fridges with family/roommates
- **Smart Inventory**: FIFO consumption tracking with expiry dates
- **Auto Unit Conversion**: Buy in packages, store in standard units
- **Split Orders**: Automatic order splitting by partner
- **Recipe Planning**: Schedule meals with ingredient checking
- **Analytics**: MongoDB-based behavior tracking

## Stopping the Application

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v
```

## Troubleshooting

**Services won't start:**
```bash
# Rebuild containers
docker compose up --build
```

**Database connection errors:**
```bash
# Check PostgreSQL is ready
docker compose logs postgres

# Restart database
docker compose restart postgres
```

**Port already in use:**
```bash
# Check what's using the port
sudo lsof -i :8000

# Modify ports in docker-compose.yml if needed
```
## License

Educational project for database course final.
