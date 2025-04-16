"""
Database verification script
This script checks if the database is properly connected and contains data
"""
import os
import sys
import logging
from app import app, db, Equipment, MaintenanceLog

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_database_connection():
    """Verify that the database connection is working"""
    try:
        # Try to execute a simple query
        result = db.session.execute('SELECT 1').scalar()
        logger.info(f"Database connection test result: {result}")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def verify_database_tables():
    """Verify that the database tables exist"""
    try:
        # Check if tables exist by inspecting metadata
        tables = db.engine.table_names()
        logger.info(f"Database tables: {tables}")
        return 'equipment' in tables and 'maintenance_log' in tables
    except Exception as e:
        logger.error(f"Error checking database tables: {e}")
        return False

def verify_database_data():
    """Verify that the database contains data"""
    try:
        # Check if there is data in the tables
        equipment_count = Equipment.query.count()
        maintenance_count = MaintenanceLog.query.count()
        
        logger.info(f"Database contains {equipment_count} equipment records and {maintenance_count} maintenance logs")
        
        # Return True if there is at least some equipment data
        return equipment_count > 0
    except Exception as e:
        logger.error(f"Error checking database data: {e}")
        return False

def print_database_info():
    """Print information about the database configuration"""
    logger.info(f"DATABASE_URL environment variable: {'Set' if os.environ.get('DATABASE_URL') else 'Not set'}")
    logger.info(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@...")
    logger.info(f"SQLALCHEMY_ENGINE_OPTIONS: {app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})}")
    logger.info(f"RENDER environment variable: {os.environ.get('RENDER', 'Not set')}")

if __name__ == "__main__":
    print_database_info()
    
    # Verify database connection
    if not verify_database_connection():
        logger.error("Database connection verification failed")
        sys.exit(1)
    
    # Verify database tables
    if not verify_database_tables():
        logger.error("Database tables verification failed")
        sys.exit(1)
    
    # Verify database data
    if not verify_database_data():
        logger.error("Database data verification failed")
        sys.exit(1)
    
    logger.info("Database verification completed successfully")
    sys.exit(0)
