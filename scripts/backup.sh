#!/bin/bash
# Backup MySQL DB and upload to S3
# Add to cron: 0 2 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1

set -e

DB_HOST="${DB_HOST}"
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
S3_BUCKET="${S3_BUCKET}"
AWS_REGION="${AWS_REGION}"

DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_FILE="/tmp/backup_${DB_NAME}_${DATE}.sql.gz"

echo "[$(date)] Starting DB backup..."
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "[$(date)] Uploading to S3..."
aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/backups/db/${DATE}.sql.gz" --region "$AWS_REGION"

rm -f "$BACKUP_FILE"
echo "[$(date)] Backup complete: backups/db/${DATE}.sql.gz"

# Delete local backups older than 7 days
find /tmp -name "backup_*.sql.gz" -mtime +7 -delete
