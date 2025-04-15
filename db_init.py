"""
Database initialization script that works with both SQLite and PostgreSQL
"""
from app import app, db, Equipment, MaintenanceLog
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# Import the equipment and log data from seed_initial_data.py
from seed_initial_data import equipment_data, log_data

def create_sample_data():
    """Create sample data for the application using seed_initial_data.py data"""
    try:
        # Log database connection info
        logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@...")
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@...")
        
        # Create tables if they don't exist
        logger.info("Creating database tables...")
        print("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
        print("Database tables created successfully")
        
        # Check if we already have data
        equipment_count = Equipment.query.count()
        logger.info(f"Current equipment count: {equipment_count}")
        print(f"Current equipment count: {equipment_count}")
        
        if equipment_count > 0:
            logger.info("Database already contains data. Skipping initialization.")
            print("Database already contains data. Skipping initialization.")
            return
        
        # Clear any existing data
        MaintenanceLog.query.delete()
        Equipment.query.delete()
        db.session.commit()
        logger.info("Existing data cleared successfully.")
        print("Existing data cleared successfully.")

        # Add equipment from seed_initial_data.py
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
                print(f"Error adding equipment {num}: {e}")
                db.session.rollback()
        
        db.session.commit()
        logger.info("Equipment data loaded successfully.")
        print("Equipment data loaded successfully.")

        # Create a mapping of equipment IDs
        equipment_map = {e.equipment_id: e.equipment_id for e in Equipment.query.all()}

        # Add maintenance logs from seed_initial_data.py
        for num, check_date, week, level, condition, filter_ok, temp, service, notes in log_data:
            if num not in equipment_map:
                logger.warning(f"Equipment {num} not found in database. Skipping log entry.")
                print(f"Equipment {num} not found in database. Skipping log entry.")
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
                print(f"Error adding maintenance log for equipment {num}: {e}")
                db.session.rollback()

        # Commit all changes
        db.session.commit()
        logger.info("✅ Equipment and maintenance log data loaded successfully.")
        print("✅ Equipment and maintenance log data loaded successfully.")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating sample data: {e}")
        print(f"Error creating sample data: {e}")
        raise

if __name__ == "__main__":
    create_sample_data()
