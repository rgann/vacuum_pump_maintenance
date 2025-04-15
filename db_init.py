"""
Database initialization script that works with both SQLite and PostgreSQL
"""
from app import app, db, Equipment, MaintenanceLog
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def get_work_week(date_obj=None):
    """Calculate the work week in YYYY-WW format."""
    if date_obj is None:
        date_obj = datetime.now()
    year = date_obj.year
    week = date_obj.isocalendar()[1]
    return f"{year}-WW{week:02d}"

def create_sample_data():
    """Create sample data for the application"""
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

        # Sample equipment data
        equipment_data = [
            {
                'equipment_id': 1,
                'equipment_name': 'Vacuum Pump 1',
                'pump_model': 'Edwards E2M28',
                'oil_type': 'Ultragrade 19',
                'pump_owner': 'John',
                'status': 'active',
                'notes': 'Main vacuum pump for chamber 1'
            },
            {
                'equipment_id': 2,
                'equipment_name': 'Vacuum Pump 2',
                'pump_model': 'Edwards E2M28',
                'oil_type': 'Ultragrade 19',
                'pump_owner': 'Sarah',
                'status': 'active',
                'notes': 'Main vacuum pump for chamber 2'
            },
            {
                'equipment_id': 3,
                'equipment_name': 'Vacuum Pump 3',
                'pump_model': 'Leybold D65B',
                'oil_type': 'LVO 100',
                'pump_owner': 'Mike',
                'status': 'active',
                'notes': 'Backup pump for chamber 1'
            },
            {
                'equipment_id': 4,
                'equipment_name': 'Vacuum Pump 4',
                'pump_model': 'Leybold D65B',
                'oil_type': 'LVO 100',
                'pump_owner': 'Lisa',
                'status': 'active',
                'notes': 'Backup pump for chamber 2'
            },
            {
                'equipment_id': 5,
                'equipment_name': 'Scroll Pump 1',
                'pump_model': 'Edwards nXDS15i',
                'oil_type': 'Scroll',
                'pump_owner': 'N/A',
                'status': 'active',
                'notes': 'Dry scroll pump for clean applications'
            },
            {
                'equipment_id': 6,
                'equipment_name': 'Spare Pump',
                'pump_model': 'Edwards E2M28',
                'oil_type': 'Ultragrade 19',
                'pump_owner': 'Jack',
                'status': 'inactive',
                'notes': 'Spare pump for emergencies'
            }
        ]

        # Add equipment
        for data in equipment_data:
            equipment = Equipment(**data)
            db.session.add(equipment)

        # Sample maintenance logs
        today = datetime.now()
        current_work_week = get_work_week(today)
        last_week = today - timedelta(days=7)
        last_work_week = get_work_week(last_week)

        # Create some maintenance logs for the current week
        maintenance_logs = [
            {
                'equipment_id': 1,
                'work_week': current_work_week,
                'check_date': today,
                'user_name': 'John',
                'oil_level_ok': True,
                'oil_condition_ok': True,
                'oil_filter_ok': True,
                'pump_temp': 65.5,
                'service': 'None Required',
                'service_notes': ''
            },
            {
                'equipment_id': 2,
                'work_week': current_work_week,
                'check_date': today,
                'user_name': 'Sarah',
                'oil_level_ok': False,
                'oil_condition_ok': True,
                'oil_filter_ok': True,
                'pump_temp': 70.2,
                'service': 'Add Oil',
                'service_notes': 'Oil level was low'
            },
            {
                'equipment_id': 3,
                'work_week': last_work_week,
                'check_date': last_week,
                'user_name': 'Mike',
                'oil_level_ok': True,
                'oil_condition_ok': False,
                'oil_filter_ok': True,
                'pump_temp': 75.8,
                'service': 'Drain & Replace Oil',
                'service_notes': 'Oil was discolored'
            }
        ]

        # Add maintenance logs
        for data in maintenance_logs:
            log = MaintenanceLog(**data)
            db.session.add(log)

        # Commit all changes
        db.session.commit()
        logger.info("Sample data created successfully")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating sample data: {e}")
        raise

if __name__ == "__main__":
    create_sample_data()
