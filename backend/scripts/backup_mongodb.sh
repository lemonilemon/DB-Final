#!/bin/bash
# =============================================================================
# MongoDB Backup Script for NEW Fridge
# =============================================================================
# Creates timestamped backups of MongoDB database (Behavior logs & Analytics)
# Usage: ./backend/scripts/backup_mongodb.sh
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
BACKUP_FILE="mongo_backup_${TIMESTAMP}.archive.gz"
DB_NAME="newfridge"
MONGO_USER="root"
MONGO_PASS="password"

echo "============================================================"
echo "NEW Fridge - MongoDB Backup"
echo "============================================================"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if MongoDB container is running
echo -e "${YELLOW}[1/3] Checking MongoDB container...${NC}"
if ! docker compose ps 2>/dev/null | grep -q "mongodb"; then
    echo -e "${RED}Error: MongoDB container is not running!${NC}"
    echo "Please start the services with: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ MongoDB container is running${NC}"
echo ""

# Create Dump
echo -e "${YELLOW}[2/3] Creating MongoDB dump...${NC}"

# We use --archive to stream the backup to a single file and --gzip to compress it
docker compose exec -T mongodb mongodump \
  --username "$MONGO_USER" \
  --password "$MONGO_PASS" \
  --authenticationDatabase admin \
  --db "$DB_NAME" \
  --archive \
  --gzip > "${BACKUP_DIR}/${BACKUP_FILE}"

BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
echo -e "${GREEN}✓ Created: ${BACKUP_FILE} (${BACKUP_SIZE})${NC}"
echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo "============================================================"
echo ""
echo "File created:"
echo "  • ${BACKUP_DIR}/${BACKUP_FILE}"
echo ""
echo "To restore this backup:"
echo "  docker compose exec -T mongodb mongorestore \\"
echo "    --username $MONGO_USER --password $MONGO_PASS \\"
echo "    --authenticationDatabase admin --nsInclude=\"${DB_NAME}.*\" \\"
echo "    --archive --gzip < ${BACKUP_DIR}/${BACKUP_FILE}"
echo ""
