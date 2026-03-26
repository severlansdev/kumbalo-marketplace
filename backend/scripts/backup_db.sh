#!/bin/bash
# KUMBALO - PostgreSQL Automated Backup Script
# Run via cron: 0 2 * * * /path/to/backup_db.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/kumbalo_backup_${TIMESTAMP}.sql.gz"

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-marketplace}"
DB_USER="${POSTGRES_USER:-postgres}"

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting backup of ${DB_NAME}..."

# Perform backup with compression
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_FILE}"

# Verify backup
if [ -s "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
    echo "[$(date)] ✅ Backup successful: ${BACKUP_FILE} (${BACKUP_SIZE})"
else
    echo "[$(date)] ❌ Backup FAILED: File is empty"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# Cleanup old backups (older than RETENTION_DAYS)
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "kumbalo_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# Count remaining backups
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/kumbalo_backup_*.sql.gz 2>/dev/null | wc -l)
echo "[$(date)] Total backups stored: ${BACKUP_COUNT}"
echo "[$(date)] Backup process complete."
