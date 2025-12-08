# Database Backup & Test Credentials

**Date Created:** December 8, 2025
**Database:** NEW Fridge PostgreSQL Database
**Total Records:** ~85,942 records

---

## Backup Files

### PostgreSQL Backup
- **SQL File:** `db_backup.sql` (5.4 MB - Uncompressed)
- **Compressed:** `db_backup.sql.gz` (1.0 MB - Gzipped)

### Automated Scripts (Recommended)

**Create a Backup:**
```bash
bash backend/scripts/backup_database.sh
```
- Creates timestamped SQL dump
- Automatically compresses backup
- Shows record counts
- Output: `db_backup_YYYYMMDD_HHMMSS.sql.gz`

**Restore from Backup:**
```bash
bash backend/scripts/restore_database.sh backend/backups/db_backup_20251208_165053.sql.gz
```
- Works with both .sql and .sql.gz files
- Automatically cleans database first
- Verifies restoration
- Shows record counts after restore

### Manual Restore Instructions

**Method 1: Using SQL file**
```bash
docker compose exec postgres psql -U postgres -d postgres < backend/backups/db_backup.sql
```

**Method 2: Using compressed file**
```bash
gunzip -c backend/backups/db_backup.sql.gz | docker compose exec -T postgres psql -U postgres -d postgres
```

**Method 3: Clean restore (drop and recreate)**
```bash
# Clean database first
docker compose exec backend python scripts/clean_data.py

# Then restore
docker compose exec postgres psql -U postgres -d postgres < backend/backups/db_backup.sql
```

---

## Test Account Credentials

All test accounts use the same password: **`password123`**

### Administrator Account

| Field       | Value                      |
|-------------|----------------------------|
| **Username**| `stanleymichael`           |
| **Email**   | `urodriguez0@example.org`  |
| **Password**| `password123`              |
| **Role**    | `Admin`                    |

**Capabilities:**
- Full access to all admin endpoints
- Can manage all users, orders, and system data
- Access to analytics and reporting

### Regular User Account #1

| Field       | Value                        |
|-------------|------------------------------|
| **Username**| `rachael013`                 |
| **Email**   | `katherine873@example.net`   |
| **Password**| `password123`                |
| **Role**    | `User`                       |

**Capabilities:**
- Manage personal fridges
- Create shopping lists
- Place orders
- Create and manage recipes
- View personal analytics

### Regular User Account #2

| Field       | Value                  |
|-------------|------------------------|
| **Username**| `hkaiser4`             |
| **Email**   | `gduke4@example.com`   |
| **Password**| `password123`          |
| **Role**    | `User`                 |

**Capabilities:**
- Same as Regular User Account #1
- Can be used to test multi-user features
- Ideal for testing fridge sharing

---

## API Authentication

To use these accounts, obtain a JWT token by calling the login endpoint:

```bash
# Login as Admin
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "stanleymichael",
    "password": "password123"
  }'

# Login as Regular User
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "rachael013",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "...",
  "user_name": "...",
  "role": "Admin" / "User"
}
```

**Using the token:**
```bash
curl -X GET http://localhost:8000/api/fridges \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Database Statistics

| Table              | Record Count |
|--------------------|--------------|
| **fridge_item**    | 50,000       |
| **order_item**     | ~25,000      |
| **store_order**    | 10,000       |
| **user**           | 500          |
| **fridge**         | 200          |
| **external_product**| 195         |
| **ingredient**     | 41           |
| **partner**        | 10           |
| **recipe**         | 4            |
| **Total**          | **~85,942**  |

### Data Characteristics

- **Users:** 500 total (3 admins, 497 regular users)
- **Ingredients:** Real-world items (vegetables, fruits, dairy, meats, grains, condiments)
- **Fridges:** 200 shared fridges with 385 access permissions
- **Fridge Items:** 50,000 items with realistic quantities and expiration dates
- **Orders:** 10,000 orders across 10 partner stores
- **Recipes:** 4 complete recipes (Scrambled Eggs, Spaghetti Carbonara, Chicken Stir Fry, Caesar Salad)

---

## Data Generation

To regenerate or create fresh data:

```bash
# Clean existing data
docker compose exec backend python scripts/clean_data.py

# Generate new data (85,000+ records)
docker compose exec backend python generate_data.py
```

**Generation time:** Approximately 3-5 minutes

---

## Notes

1. **Password Security:** All test accounts use `password123` which is bcrypt-hashed in the database
2. **Realistic Data:** Generated using Faker library for realistic names, emails, and data patterns
3. **Foreign Keys:** All relationships are properly maintained with CASCADE/RESTRICT rules
4. **Expiration Dates:** Fridge items have realistic expiration dates based on ingredient shelf life
5. **Order History:** Orders span the last 90 days with various statuses (Pending, Paid, Shipped, Delivered, Cancelled)

---

## Uploading Backups

### Recommended Platforms

1. **Google Drive / Dropbox**
   - Upload `db_backup.sql.gz` (1.0 MB - smaller file)
   - Share link with read permissions

2. **GitHub Repository**
   - Add to `.gitignore` if file is too large
   - Use Git LFS for files > 100 MB
   - Or use GitHub Releases for large files

3. **Cloud Storage (AWS S3, Azure Blob)**
   - For production deployments
   - Set appropriate access controls

### Example Upload Commands

**Google Drive (using gdrive CLI):**
```bash
gdrive upload backend/backups/db_backup.sql.gz
```

**AWS S3:**
```bash
aws s3 cp backend/backups/db_backup.sql.gz s3://your-bucket/db-backups/
```

**Git LFS:**
```bash
git lfs track "*.sql.gz"
git add backend/backups/db_backup.sql.gz
git commit -m "Add database backup"
git push
```

---

## Support

For issues or questions about the backup or test accounts, please refer to the main project documentation or contact the development team.

**Last Updated:** December 8, 2025
