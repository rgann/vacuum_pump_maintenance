"""
Script to migrate data from Render PostgreSQL to Supabase PostgreSQL
"""
import os
import sys
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import Supabase configuration first
from supabase_config import get_db_connection_string, test_db_connection

# Import app and models after environment variables are loaded
# But don't use them directly outside of functions
from app import app

def backup_current_data():
    """Backup current data to a JSON file"""
    try:
        # Import models within the function to ensure they're used within app context
        from app import db, Equipment, MaintenanceLog

        logger.info("Backing up current data...")

        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamp for backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'migration_backup_{timestamp}.json')

        # Get database URI from app config
        with app.app_context():
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            masked_uri = db_uri.split('@')[0] + '@...' if '@' in db_uri else db_uri

            # Collect data from all tables
            backup_data = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'source': masked_uri
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

        logger.info(f"Backup completed successfully: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Error backing up data: {e}")
        return None

def setup_supabase_database():
    """Set up the Supabase database schema"""
    try:
        # Import models within the function to ensure they're used within app context
        from app import db

        logger.info("Setting up Supabase database schema...")

        # Create tables within app context
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")

        return True
    except Exception as e:
        logger.error(f"Error setting up Supabase database: {e}")
        return False

def migrate_data(backup_file):
    """Migrate data from backup file to Supabase"""
    try:
        # Import models within the function to ensure they're used within app context
        from app import db, Equipment, MaintenanceLog

        logger.info(f"Migrating data from backup file: {backup_file}")

        # Read backup file
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)

        # Check if backup file has expected structure
        if 'tables' not in backup_data:
            logger.error("Invalid backup file format: 'tables' key not found")
            return False

        # Perform database operations within app context
        with app.app_context():
            # Begin transaction
            db.session.begin_nested()

            # Migrate Equipment table
            equipment_count = 0
            if 'equipment' in backup_data['tables']:
                for item_data in backup_data['tables']['equipment']:
                    # Check if equipment already exists
                    existing = Equipment.query.filter_by(equipment_id=item_data['equipment_id']).first()
                    if existing:
                        # Update existing equipment
                        for key, value in item_data.items():
                            setattr(existing, key, value)
                    else:
                        # Create new equipment
                        item = Equipment(**item_data)
                        db.session.add(item)
                    equipment_count += 1

            # Migrate MaintenanceLog table
            logs_count = 0
            if 'maintenance_logs' in backup_data['tables']:
                for log_data in backup_data['tables']['maintenance_logs']:
                    # Convert date string back to date object
                    if log_data.get('check_date'):
                        log_data['check_date'] = datetime.fromisoformat(log_data['check_date']).date()

                    # Check if log already exists
                    existing = MaintenanceLog.query.filter_by(log_id=log_data['log_id']).first()
                    if existing:
                        # Update existing log
                        for key, value in log_data.items():
                            setattr(existing, key, value)
                    else:
                        # Create new log
                        log = MaintenanceLog(**log_data)
                        db.session.add(log)
                    logs_count += 1

            # Commit transaction
            db.session.commit()

            logger.info(f"Data migration completed successfully: {equipment_count} equipment records, {logs_count} maintenance logs")
            return True
    except Exception as e:
        # Rollback transaction if possible
        try:
            with app.app_context():
                db.session.rollback()
        except Exception:
            pass  # Ignore errors during rollback
        logger.error(f"Error migrating data: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    try:
        # Import models within the function to ensure they're used within app context
        from app import db, Equipment, MaintenanceLog

        logger.info("Verifying migration...")

        # Count records in tables within app context
        with app.app_context():
            equipment_count = Equipment.query.count()
            maintenance_count = MaintenanceLog.query.count()

            logger.info(f"Verification results: {equipment_count} equipment records, {maintenance_count} maintenance logs")

            # Return True if there is at least some data
            return equipment_count > 0
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        return False

def run_migration():
    """Run the migration process within an application context"""
    try:
        # Check if Supabase connection is configured
        if not get_db_connection_string():
            logger.error("Supabase database connection not configured. Please set the required environment variables.")
            return False

        # Test Supabase connection
        logger.info("Testing Supabase database connection...")
        if not test_db_connection():
            logger.error("Failed to connect to Supabase database. Please check your configuration.")
            return False

        logger.info("Supabase database connection successful")

        # Backup current data
        backup_file = backup_current_data()
        if not backup_file:
            logger.error("Failed to backup current data. Migration aborted.")
            return False

        # Set up Supabase database schema
        if not setup_supabase_database():
            logger.error("Failed to set up Supabase database schema. Migration aborted.")
            return False

        # Migrate data
        if not migrate_data(backup_file):
            logger.error("Failed to migrate data to Supabase. Migration aborted.")
            return False

        # Verify migration
        if not verify_migration():
            logger.error("Migration verification failed. Please check the logs for details.")
            return False

        logger.info("Migration to Supabase completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False

if __name__ == "__main__":
    # Run the migration within a Flask application context
    with app.app_context():
        success = run_migration()
        sys.exit(0 if success else 1)
