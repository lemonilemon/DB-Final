#!/bin/bash
# =============================================================================
# MongoDB Restore Script for NEW Fridge
# =============================================================================
# Restores MongoDB database from a .archive.gz backup file
# Usage: ./backend/scripts/restore_mongodb.sh <backup_file_name>
# Example: ./backend/scripts/restore_mongodb.sh mongo_backup_20251209_120000.archive.gz
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backend/backups"
DB_NAME="newfridge"
MONGO_USER="root"
MONGO_PASS="password"

echo "============================================================"
echo "NEW Fridge - MongoDB Restore"
echo "============================================================"
echo ""

# Check argument
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified.${NC}"
    echo "Usage: $0 <backup_filename>"
    echo ""
    echo "Available backups in ${BACKUP_DIR}:
    ls -1 "${BACKUP_DIR}" | grep "mongo_backup"
    exit 1
fi

BACKUP_FILE="${BACKUP_DIR}/$1"

# Check if file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

# Check if MongoDB container is running
echo -e "${YELLOW}[1/3] Checking MongoDB container...${NC}"
if ! docker compose ps 2>/dev/null | grep -q "mongodb"; then
    echo -e "${RED}Error: MongoDB container is not running!${NC}"
    echo "Please start the services with: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ MongoDB container is running${NC}"
echo ""

# Confirm Restore
echo -e "${YELLOW}WARNING: This will overwrite data in the '${DB_NAME}' database.${NC}"
echo -e "Backup file: ${BACKUP_FILE}"
read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi
echo ""

# Restore
echo -e "${YELLOW}[2/3] Restoring database...${NC}"

# We use mongorestore with --archive and --gzip
# --drop ensures the existing collections are dropped before restoring
docker compose exec -T mongodb mongorestore \
  --username "$MONGO_USER" \
  --password "$MONGO_PASS" \
  --authenticationDatabase admin \
  --nsInclude="${DB_NAME}.*" \
  --drop \
  --archive \
  --gzip < "${BACKUP_FILE}"

echo -e "${GREEN}✓ Restore process completed${NC}"
echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}Database restored successfully!${NC}"
echo "============================================================"
echo ""
