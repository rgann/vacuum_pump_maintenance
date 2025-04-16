# Database Backups

This directory contains database backups for the Vacuum Pump Maintenance application.

## Backup Format

Backups are stored as JSON files with the following naming convention:
```
db_backup_YYYYMMDD_HHMMSS.json
```

## Backup Contents

Each backup file contains:
- Equipment data
- Maintenance log data
- Metadata about when the backup was created

## Restoring from Backup

To restore from a backup, use the `/restore-db/<filename>` endpoint.

## Automatic Backups

The application automatically creates a backup every 24 hours and keeps the 10 most recent backups.

## Manual Backups

You can manually create a backup by visiting the `/backup-db` endpoint.
