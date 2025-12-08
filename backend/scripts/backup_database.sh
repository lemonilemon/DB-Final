#!/bin/bash
# =============================================================================
# Database Backup Script for NEW Fridge
# =============================================================================
# Creates timestamped backups of PostgreSQL database
# Usage: ./backend/scripts/backup_database.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backend/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="db_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="db_backup_${TIMESTAMP}.sql.gz"

echo "============================================================"
echo "NEW Fridge - Database Backup"
echo "============================================================"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if PostgreSQL container is running
echo -e "${YELLOW}[1/4] Checking PostgreSQL container...${NC}"
if ! docker compose ps 2>/dev/null | grep -q "postgres"; then
    echo -e "${RED}Error: PostgreSQL container is not running!${NC}"
    echo "Please start the services with: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
echo ""

# Create SQL dump
echo -e "${YELLOW}[2/4] Creating database dump...${NC}"
docker compose exec -T postgres pg_dump -U postgres -d postgres > "${BACKUP_DIR}/${BACKUP_FILE}"
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
echo -e "${GREEN}✓ Created: ${BACKUP_FILE} (${BACKUP_SIZE})${NC}"
echo ""

# Compress backup
echo -e "${YELLOW}[3/4] Compressing backup...${NC}"
gzip -c "${BACKUP_DIR}/${BACKUP_FILE}" > "${BACKUP_DIR}/${COMPRESSED_FILE}"
COMPRESSED_SIZE=$(du -h "${BACKUP_DIR}/${COMPRESSED_FILE}" | cut -f1)
echo -e "${GREEN}✓ Created: ${COMPRESSED_FILE} (${COMPRESSED_SIZE})${NC}"
echo ""

# Show statistics
echo -e "${YELLOW}[4/4] Backup statistics...${NC}"
RECORD_COUNT=$(docker compose exec -T postgres psql -U postgres -d postgres -t -c "
    SELECT
        SUM(count) as total
    FROM (
        SELECT COUNT(*) as count FROM \"user\"
        UNION ALL SELECT COUNT(*) FROM ingredient
        UNION ALL SELECT COUNT(*) FROM fridge
        UNION ALL SELECT COUNT(*) FROM fridge_item
        UNION ALL SELECT COUNT(*) FROM partner
        UNION ALL SELECT COUNT(*) FROM external_product
        UNION ALL SELECT COUNT(*) FROM store_order
        UNION ALL SELECT COUNT(*) FROM order_item
        UNION ALL SELECT COUNT(*) FROM recipe
        UNION ALL SELECT COUNT(*) FROM shopping_list_item
    ) counts;
" | xargs)

echo -e "${GREEN}✓ Total records backed up: ${RECORD_COUNT}${NC}"
echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo "============================================================"
echo ""
echo "Files created:"
echo "  • ${BACKUP_DIR}/${BACKUP_FILE} (${BACKUP_SIZE})"
echo "  • ${BACKUP_DIR}/${COMPRESSED_FILE} (${COMPRESSED_SIZE})"
echo ""
echo "To restore this backup:"
echo "  ./backend/scripts/restore_database.sh ${BACKUP_FILE}"
echo ""
echo "Or use the compressed version:"
echo "  ./backend/scripts/restore_database.sh ${COMPRESSED_FILE}"
echo ""
