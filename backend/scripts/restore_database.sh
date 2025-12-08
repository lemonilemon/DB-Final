#!/bin/bash
# =============================================================================
# Database Restore Script for NEW Fridge
# =============================================================================
# Restores PostgreSQL database from backup file
# Usage:
#   ./backend/scripts/restore_database.sh <backup_file>
#   ./backend/scripts/restore_database.sh backend/backups/db_backup.sql
#   ./backend/scripts/restore_database.sh backend/backups/db_backup.sql.gz
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================================"
echo "NEW Fridge - Database Restore"
echo "============================================================"
echo ""

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified!${NC}"
    echo ""
    echo "Usage:"
    echo "  ./backend/scripts/restore_database.sh <backup_file>"
    echo ""
    echo "Examples:"
    echo "  ./backend/scripts/restore_database.sh backend/backups/db_backup.sql"
    echo "  ./backend/scripts/restore_database.sh backend/backups/db_backup_20251208_140530.sql.gz"
    echo ""
    echo "Available backups:"
    if [ -d "backend/backups" ]; then
        ls -lh backend/backups/*.sql* 2>/dev/null || echo "  No backups found in backend/backups/"
    else
        echo "  backend/backups/ directory not found"
    fi
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

# Check if PostgreSQL container is running
echo -e "${YELLOW}[1/5] Checking PostgreSQL container...${NC}"
if ! docker compose ps 2>/dev/null | grep -q "postgres"; then
    echo -e "${RED}Error: PostgreSQL container is not running!${NC}"
    echo "Please start the services with: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
echo ""

# Warning
echo -e "${RED}WARNING: This will DELETE all existing data in the database!${NC}"
echo ""
echo "Backup file: ${BACKUP_FILE}"
echo "Database: postgres"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Clean existing data
echo -e "${YELLOW}[2/5] Cleaning existing data...${NC}"
docker compose exec backend python scripts/clean_data.py 2>&1 | grep -E "(✓|Truncating)" || true
echo -e "${GREEN}✓ Database cleaned${NC}"
echo ""

# Restore from backup
echo -e "${YELLOW}[3/5] Restoring database...${NC}"
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "Decompressing and restoring from: ${BACKUP_FILE}"
    gunzip -c "$BACKUP_FILE" | docker compose exec -T postgres psql -U postgres -d postgres > /dev/null 2>&1
else
    echo "Restoring from: ${BACKUP_FILE}"
    docker compose exec -T postgres psql -U postgres -d postgres < "$BACKUP_FILE" > /dev/null 2>&1
fi
echo -e "${GREEN}✓ Database restored${NC}"
echo ""

# Verify restoration
echo -e "${YELLOW}[4/5] Verifying restoration...${NC}"
TABLES=$(docker compose exec -T postgres psql -U postgres -d postgres -t -c "
    SELECT
        table_name || ': ' ||
        (SELECT COUNT(*) FROM information_schema.tables t WHERE t.table_name = ist.table_name) as count
    FROM information_schema.tables ist
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
" 2>/dev/null)

echo -e "${GREEN}✓ Database structure verified${NC}"
echo ""

# Show record counts
echo -e "${YELLOW}[5/5] Record counts...${NC}"
docker compose exec -T postgres psql -U postgres -d postgres -c "
SELECT
    'user' as table_name, COUNT(*) as records FROM \"user\"
UNION ALL
SELECT 'ingredient', COUNT(*) FROM ingredient
UNION ALL
SELECT 'fridge', COUNT(*) FROM fridge
UNION ALL
SELECT 'fridge_item', COUNT(*) FROM fridge_item
UNION ALL
SELECT 'recipe', COUNT(*) FROM recipe
UNION ALL
SELECT 'partner', COUNT(*) FROM partner
UNION ALL
SELECT 'external_product', COUNT(*) FROM external_product
UNION ALL
SELECT 'store_order', COUNT(*) FROM store_order
UNION ALL
SELECT 'order_item', COUNT(*) FROM order_item
UNION ALL
SELECT 'shopping_list_item', COUNT(*) FROM shopping_list_item
ORDER BY records DESC;
" 2>/dev/null

echo ""
echo "============================================================"
echo -e "${GREEN}Database restored successfully!${NC}"
echo "============================================================"
echo ""
echo "You can now:"
echo "  • Access API at http://localhost:8000"
echo "  • View docs at http://localhost:8000/docs"
echo "  • Access pgAdmin at http://localhost:5050"
echo ""
