"""
Direct database initialization script for Render deployment.
This script directly creates and populates the SQLite database.
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta
import random

# Use the database in the current directory for simplicity
db_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(db_dir, "vacuum_pump_maintenance.db")
print(f"Database path: {db_path}")

# Check if database already exists and has data
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if equipment table exists and has data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM equipment")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Database already contains {count} equipment records. Setup skipped.")
            conn.close()
            sys.exit(0)
except Exception as e:
    print(f"Error checking database: {e}")
    # Continue with setup even if there was an error checking

# Create tables
print("Creating database tables...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create equipment table
cursor.execute('''
CREATE TABLE IF NOT EXISTS equipment (
    equipment_id INTEGER PRIMARY KEY,
    equipment_name TEXT NOT NULL,
    pump_model TEXT,
    oil_type TEXT,
    pump_owner TEXT,
    status TEXT DEFAULT 'active',
    notes TEXT
)
''')

# Create maintenance_log table
cursor.execute('''
CREATE TABLE IF NOT EXISTS maintenance_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    work_week TEXT NOT NULL,
    check_date DATE NOT NULL,
    user_name TEXT,
    oil_level_ok BOOLEAN,
    oil_condition_ok BOOLEAN,
    oil_filter_ok BOOLEAN,
    pump_temp REAL,
    service TEXT,
    service_notes TEXT,
    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id) ON DELETE CASCADE
)
''')

# Sample equipment data (equipment_id, equipment_name, pump_model, oil_type, pump_owner, status, notes)
equipment_data = [
    (1, "JR Intake GB", "JR-2000", "Synthetic 20W", "Engineering", "active", "Main intake pump"),
    (2, "Spot/Sonic Weld GB", "SW-500", "Mineral 10W", "Production", "active", "Requires weekly checks"),
    (3, "Elyte GB", "EL-1000", "Synthetic 30W", "R&D", "active", "New installation"),
    (4, "Chem GB 005", "CG-005", "Synthetic 20W", "Chemistry", "active", "Sensitive to temperature"),
    (5, "Chem GB 006", "CG-006", "Synthetic 20W", "Chemistry", "active", "Backup for CG-005"),
    (6, "GCMS", "GC-2000", "Mineral 15W", "Analytics", "active", "Critical system"),
    (7, "GCMS panel", "GCP-100", "Mineral 15W", "Analytics", "active", "Connected to GCMS"),
    (8, "Gas Pump/Goop Transfer", "GP-500", "Synthetic 40W", "Production", "active", "High temperature operation"),
    (9, "Jupiter", "JP-1000", "Synthetic 20W", "R&D", "active", "Experimental setup"),
    (10, "Olympus", "OL-2000", "Mineral 10W", "Engineering", "active", "Main production line")
]

# Insert equipment data
print("Inserting equipment data...")
cursor.executemany(
    "INSERT INTO equipment (equipment_id, equipment_name, pump_model, oil_type, pump_owner, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
    equipment_data
)

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
print("Generating maintenance logs...")
services = ["None Required", "Add Oil", "Drain & Replace Oil", "Replace Filter", "Clean Pump", "Major Service"]
maintenance_logs = []

for equipment_id, _, _, _, _ in equipment_data:
    for i, work_week in enumerate(work_weeks):
        # Skip some entries to make data more realistic
        if random.random() < 0.2:
            continue

        # Generate random data
        check_date = (today - timedelta(weeks=i, days=random.randint(0, 6))).strftime('%Y-%m-%d')
        oil_level_ok = 1 if random.random() > 0.2 else 0
        oil_condition_ok = 1 if random.random() > 0.2 else 0
        oil_filter_ok = 1 if random.random() > 0.2 else 0
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

        maintenance_logs.append((
            equipment_id,
            work_week,
            check_date,
            "System",
            oil_level_ok,
            oil_condition_ok,
            oil_filter_ok,
            pump_temp,
            service,
            "Initial setup data"
        ))

# Insert maintenance logs
cursor.executemany(
    """
    INSERT INTO maintenance_log
    (equipment_id, work_week, check_date, user_name, oil_level_ok, oil_condition_ok, oil_filter_ok, pump_temp, service, service_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    maintenance_logs
)

# Commit changes and close connection
conn.commit()
print(f"Inserted {len(equipment_data)} equipment records and {len(maintenance_logs)} maintenance logs.")
conn.close()

print("Database initialization completed successfully!")
