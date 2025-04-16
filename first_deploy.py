"""
First deployment script for initializing the database
This script should only run once when the database is first created
"""
import os
import sys
import logging
from app import db, Equipment, MaintenanceLog
from db_init import create_sample_data

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_first_deploy():
    """Check if this is the first deployment by looking for a marker file"""
    marker_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.db_initialized')
    return not os.path.exists(marker_file)

def mark_as_initialized():
    """Create a marker file to indicate that the database has been initialized"""
    marker_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.db_initialized')
    with open(marker_file, 'w') as f:
        f.write(f"Database initialized at {os.environ.get('RENDER_EXTERNAL_URL', 'unknown')}")
    logger.info(f"Created marker file at {marker_file}")

def check_database():
    """Check if the database has tables and data"""
    try:
        # Check if tables exist
        equipment_count = Equipment.query.count()
        logger.info(f"Found {equipment_count} equipment records in database")
        return equipment_count > 0
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

def initialize_database():
    """Initialize the database with sample data"""
    try:
        logger.info("Starting database initialization")
        
        # Create tables
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Add sample data
        create_sample_data()
        
        # Mark as initialized
        mark_as_initialized()
        
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    try:
        logger.info("Checking if this is the first deployment")
        
        # Check if this is the first deployment
        if is_first_deploy():
            logger.info("This appears to be the first deployment")
            
            # Check if database already has data
            if check_database():
                logger.info("Database already has data, marking as initialized")
                mark_as_initialized()
            else:
                logger.info("Database is empty, initializing with sample data")
                if initialize_database():
                    logger.info("Database initialization successful")
                    sys.exit(0)
                else:
                    logger.error("Database initialization failed")
                    sys.exit(1)
        else:
            logger.info("Not the first deployment, skipping initialization")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
