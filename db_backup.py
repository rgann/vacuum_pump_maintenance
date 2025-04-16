"""
Database backup utility for PostgreSQL databases
"""
import os
import json
import logging
import datetime
from app import app, db, Equipment, MaintenanceLog

logger = logging.getLogger(__name__)

def backup_database():
    """Create a JSON backup of all database data"""
    try:
        logger.info("Starting database backup...")
        
        # Get database connection information
        db_type = "PostgreSQL" if "postgresql" in app.config['SQLALCHEMY_DATABASE_URI'] else "SQLite"
        logger.info(f"Database type: {db_type}")
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate timestamp for backup filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
        
        # Collect data from all tables
        backup_data = {
            'metadata': {
                'timestamp': datetime.datetime.now().isoformat(),
                'database_type': db_type
            },
            'tables': {}
        }
        
        # Backup Equipment table
        equipment_list = []
        for item in Equipment.query.all():
            equipment_list.append({
                'equipment_id': item.equipment_id,
                'equipment_name': item.equipment_name,
                'pump_model': item.pump_model,
                'oil_type': item.oil_type,
                'pump_owner': item.pump_owner,
                'status': item.status,
                'notes': item.notes
            })
        backup_data['tables']['equipment'] = equipment_list
        logger.info(f"Backed up {len(equipment_list)} equipment records")
        
        # Backup MaintenanceLog table
        logs_list = []
        for log in MaintenanceLog.query.all():
            logs_list.append({
                'log_id': log.log_id,
                'equipment_id': log.equipment_id,
                'work_week': log.work_week,
                'check_date': log.check_date.isoformat() if log.check_date else None,
                'user_name': log.user_name,
                'oil_level_ok': log.oil_level_ok,
                'oil_condition_ok': log.oil_condition_ok,
                'oil_filter_ok': log.oil_filter_ok,
                'pump_temp': log.pump_temp,
                'service': log.service,
                'service_notes': log.service_notes
            })
        backup_data['tables']['maintenance_logs'] = logs_list
        logger.info(f"Backed up {len(logs_list)} maintenance log records")
        
        # Write backup to file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Database backup completed successfully: {backup_file}")
        return {
            'status': 'success',
            'file': backup_file,
            'equipment_count': len(equipment_list),
            'logs_count': len(logs_list)
        }
        
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

def restore_database(backup_file):
    """Restore database from JSON backup file"""
    try:
        logger.info(f"Starting database restore from {backup_file}...")
        
        # Read backup file
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Check if backup file has expected structure
        if 'tables' not in backup_data:
            raise ValueError("Invalid backup file format: 'tables' key not found")
        
        # Begin transaction
        db.session.begin_nested()
        
        # Clear existing data
        MaintenanceLog.query.delete()
        Equipment.query.delete()
        db.session.flush()
        
        # Restore Equipment table
        equipment_count = 0
        if 'equipment' in backup_data['tables']:
            for item_data in backup_data['tables']['equipment']:
                item = Equipment(**item_data)
                db.session.add(item)
                equipment_count += 1
        
        # Restore MaintenanceLog table
        logs_count = 0
        if 'maintenance_logs' in backup_data['tables']:
            for log_data in backup_data['tables']['maintenance_logs']:
                # Convert date string back to date object
                if log_data.get('check_date'):
                    log_data['check_date'] = datetime.datetime.fromisoformat(log_data['check_date']).date()
                
                log = MaintenanceLog(**log_data)
                db.session.add(log)
                logs_count += 1
        
        # Commit transaction
        db.session.commit()
        
        logger.info(f"Database restore completed successfully: {equipment_count} equipment records, {logs_count} maintenance logs")
        return {
            'status': 'success',
            'equipment_count': equipment_count,
            'logs_count': logs_count
        }
        
    except Exception as e:
        # Rollback transaction
        db.session.rollback()
        logger.error(f"Error restoring database: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

if __name__ == "__main__":
    backup_result = backup_database()
    print(json.dumps(backup_result, indent=2))
