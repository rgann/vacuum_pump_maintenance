"""
This script is specifically for initializing the database on Render.
It ensures the database directory exists and is populated with sample data.
"""
import os
import sys
from pathlib import Path
from app import app, db, Equipment, MaintenanceLog
from datetime import datetime, timedelta
import random

def ensure_data_directory():
    """Ensure the data directory exists"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    print(f"Data directory created/verified: {data_dir}")
    return data_dir

def create_sample_data():
    """Create sample data in the database"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Print database path for debugging
        print(f"Database path: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Check if we already have data
        equipment_count = Equipment.query.count()
        print(f"Found {equipment_count} equipment records in database")
        
        if equipment_count > 0:
            print("Database already contains data. Setup skipped.")
            return
            
        print("Database is empty. Creating sample data...")
        
        # Sample equipment data
        equipment_data = [
            {"equipment_id": 1, "equipment_name": "JR Intake GB", "location": "Building A", "model": "JR-2000", "serial_number": "JR2023001"},
            {"equipment_id": 2, "equipment_name": "Spot/Sonic Weld GB", "location": "Building A", "model": "SW-500", "serial_number": "SW2023002"},
            {"equipment_id": 3, "equipment_name": "Elyte GB", "location": "Building B", "model": "EL-1000", "serial_number": "EL2023003"},
            {"equipment_id": 4, "equipment_name": "Chem GB 005", "location": "Building B", "model": "CG-005", "serial_number": "CG2023004"},
            {"equipment_id": 5, "equipment_name": "Chem GB 006", "location": "Building C", "model": "CG-006", "serial_number": "CG2023005"},
            {"equipment_id": 6, "equipment_name": "GCMS", "location": "Building C", "model": "GC-2000", "serial_number": "GC2023006"},
            {"equipment_id": 7, "equipment_name": "GCMS panel", "location": "Building D", "model": "GCP-100", "serial_number": "GCP2023007"},
            {"equipment_id": 8, "equipment_name": "Gas Pump/Goop Transfer", "location": "Building D", "model": "GP-500", "serial_number": "GP2023008"},
            {"equipment_id": 9, "equipment_name": "Jupiter", "location": "Building E", "model": "JP-1000", "serial_number": "JP2023009"},
            {"equipment_id": 10, "equipment_name": "Olympus", "location": "Building E", "model": "OL-2000", "serial_number": "OL2023010"}
        ]
        
        # Add equipment
        for data in equipment_data:
            equipment = Equipment(**data)
            db.session.add(equipment)
        
        # Generate work weeks for the past 8 weeks
        today = datetime.now()
        work_weeks = []
        for i in range(8):
            date = today - timedelta(weeks=i)
            year = date.year
            week = date.isocalendar()[1]
            work_week = f"{year}-WW{week:02d}"
            work_weeks.append(work_week)
        
        # Generate maintenance logs
        services = ["None Required", "Add Oil", "Drain & Replace Oil", "Replace Filter", "Clean Pump", "Major Service"]
        
        for equipment in equipment_data:
            for i, work_week in enumerate(work_weeks):
                # Skip some entries to make data more realistic
                if random.random() < 0.2:
                    continue
                
                # Generate random data
                check_date = today - timedelta(weeks=i, days=random.randint(0, 6))
                oil_level_ok = random.random() > 0.2
                oil_condition_ok = random.random() > 0.2
                oil_filter_ok = random.random() > 0.2
                pump_temp = random.uniform(60, 85)
                
                # Determine service based on conditions
                if not oil_level_ok and not oil_condition_ok:
                    service = "Drain & Replace Oil"
                elif not oil_level_ok:
                    service = "Add Oil"
                elif not oil_filter_ok:
                    service = "Replace Filter"
                else:
                    service = random.choice(services)
                
                # Create log entry
                log = MaintenanceLog(
                    equipment_id=equipment["equipment_id"],
                    work_week=work_week,
                    check_date=check_date,
                    user_name="System",
                    oil_level_ok=oil_level_ok,
                    oil_condition_ok=oil_condition_ok,
                    oil_filter_ok=oil_filter_ok,
                    pump_temp=pump_temp,
                    service=service,
                    service_notes="Initial setup data"
                )
                db.session.add(log)
        
        # Commit all changes
        db.session.commit()
        print("Database initialized with sample data.")

if __name__ == "__main__":
    print("Starting Render database initialization...")
    data_dir = ensure_data_directory()
    create_sample_data()
    print("Render database initialization completed successfully!")
