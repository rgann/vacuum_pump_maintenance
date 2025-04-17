"""
Script to check if data exists in the database
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('check_data.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import app and models
from app import app

def check_data():
    """Check if data exists in the database"""
    try:
        # Import models within app context
        with app.app_context():
            from app import db, Equipment, MaintenanceLog
            
            # Check if tables exist
            try:
                equipment_count = Equipment.query.count()
                maintenance_count = MaintenanceLog.query.count()
                
                logger.info(f"Equipment count: {equipment_count}")
                logger.info(f"Maintenance logs count: {maintenance_count}")
                
                if equipment_count == 0 and maintenance_count == 0:
                    logger.warning("No data found in the database!")
                    return False
                else:
                    logger.info("Data found in the database.")
                    
                    # Print some sample data
                    if equipment_count > 0:
                        sample_equipment = Equipment.query.first()
                        logger.info(f"Sample equipment: {sample_equipment.equipment_name} (ID: {sample_equipment.equipment_id})")
                    
                    if maintenance_count > 0:
                        sample_log = MaintenanceLog.query.first()
                        logger.info(f"Sample maintenance log: Equipment ID {sample_log.equipment_id}, Date: {sample_log.check_date}")
                    
                    return True
            except Exception as e:
                logger.error(f"Error querying tables: {e}")
                return False
    except Exception as e:
        logger.error(f"Error checking data: {e}")
        return False

if __name__ == "__main__":
    # Run the check
    success = check_data()
    sys.exit(0 if success else 1)
