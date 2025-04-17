"""
Script to populate Supabase database with seed data
"""
import os
import sys
import logging
from datetime import datetime, date
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('supabase_populate.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import app and models
from app import app
from seed_initial_data import equipment_data, log_data

def populate_supabase():
    """Populate Supabase database with seed data"""
    try:
        # Import models within app context
        with app.app_context():
            from app import db, Equipment, MaintenanceLog
            
            logger.info("Starting to populate Supabase database with seed data...")
            
            # Check if database is already populated
            equipment_count = Equipment.query.count()
            if equipment_count > 0:
                logger.info(f"Database already contains {equipment_count} equipment records.")
                user_input = input("Database already contains data. Do you want to clear it and repopulate? (y/n): ")
                if user_input.lower() != 'y':
                    logger.info("Operation cancelled by user.")
                    return False
                
                # Clear existing data
                logger.info("Clearing existing data...")
                MaintenanceLog.query.delete()
                Equipment.query.delete()
                db.session.commit()
                logger.info("Existing data cleared successfully.")
            
            # Add equipment data
            logger.info("Adding equipment data...")
            for num, name, model, oil, owner, status, notes in equipment_data:
                try:
                    e = Equipment(
                        equipment_id=num,
                        equipment_name=name,
                        pump_model=model,
                        oil_type=oil,
                        pump_owner=owner,
                        status=status,
                        notes=notes
                    )
                    db.session.add(e)
                except Exception as e:
                    logger.error(f"Error adding equipment {num}: {e}")
                    db.session.rollback()
            
            db.session.commit()
            logger.info("Equipment data loaded successfully.")
            
            # Create a mapping of equipment IDs
            equipment_map = {e.equipment_id: e.equipment_id for e in Equipment.query.all()}
            
            # Add maintenance logs
            logger.info("Adding maintenance logs...")
            for num, check_date, week, level, condition, filter_ok, temp, service, notes in log_data:
                if num not in equipment_map:
                    logger.warning(f"Equipment {num} not found in database. Skipping log entry.")
                    continue
                
                try:
                    log = MaintenanceLog(
                        equipment_id=equipment_map[num],
                        work_week=week,
                        check_date=check_date,
                        oil_level_ok=level,
                        oil_condition_ok=condition,
                        oil_filter_ok=filter_ok,
                        pump_temp=temp,
                        service=service,
                        service_notes=notes
                    )
                    db.session.add(log)
                except Exception as e:
                    logger.error(f"Error adding maintenance log for equipment {num}: {e}")
                    db.session.rollback()
            
            db.session.commit()
            
            # Verify data was added
            equipment_count = Equipment.query.count()
            log_count = MaintenanceLog.query.count()
            
            logger.info(f"✅ Database populated successfully with {equipment_count} equipment records and {log_count} maintenance logs.")
            return True
            
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        return False

if __name__ == "__main__":
    # Run the population script within a Flask application context
    success = populate_supabase()
    sys.exit(0 if success else 1)
