from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vacuum_pump_maintenance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Equipment(db.Model):
    equipment_id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='active')
    pump_model = db.Column(db.String(100))
    oil_type = db.Column(db.String(100))
    pump_owner = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    maintenance_logs = db.relationship('MaintenanceLog', backref='equipment', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Equipment({self.equipment_id}: {self.equipment_name})"

class MaintenanceLog(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.equipment_id', ondelete='CASCADE'), nullable=False)
    work_week = db.Column(db.String(10))
    check_date = db.Column(db.Date, nullable=False)
    user_name = db.Column(db.String(100))
    oil_level_ok = db.Column(db.Boolean, default=False)
    oil_condition_ok = db.Column(db.Boolean, default=False)
    oil_filter_ok = db.Column(db.Boolean, default=False)
    pump_temp = db.Column(db.Float)
    service = db.Column(db.String(50), default='None Required')
    service_notes = db.Column(db.Text)

    def __repr__(self):
        return f"MaintenanceLog({self.log_id}: {self.check_date} for Equipment {self.equipment_id})"

equipment_data = [
    (1, 'JR intake GB','Edwards RV12', 'Oil', 'Mfg (Jonathan)','Active', ''),
    (2, 'Spot/Sonic Weld GB', 'Edwards RV12', 'Oil', 'Mfg (Jonathan)','Active', ''),
    (3, 'Laser Weld GB', None, 'Scroll', 'N/A','Active', ''),
    (4, 'Laser Weld GB', None, 'Scroll', 'N/A','Active', ''),
    (5, 'Laser Weld GB', None, 'Scroll', 'N/A','Active', ''),
    (6, 'Elyte GB', 'Edwards RV12', 'Ultra Grade 19', 'Mfg (Fernando)','Active', ''),
    (7, 'Chem GB 005', 'Edwards RV12', 'Ultra Grade 19', 'Mfg (Jonathan)','Active', ''),
    (8, 'Chem GB 006', 'Edwards RV12', 'Ultra Grade 19', 'Mfg (Jonathan)','Active', ''),
    (9, 'GCMS','Edwards RV3', 'Ultra Grade 19', 'Chem (Jeremy)','Active', ''),
    (10, 'GCMS panel', 'Edwards RV8', 'Ultra Grade 19', 'Chem (Jeremy)','Active', ''),
    (11, 'Gas Pump/Goop Transfer', 'Edwards RV5', 'Ultra Grade 19', 'Process (Ben)','Active', ''),
    (12, 'Jupiter','Edwards RV8', 'Ultra Grade 19', 'Mfg (Fernando)','Active', ''),
    (13, 'Olympus', 'Edwards RV8', 'Ultra Grade 19', 'Mfg (Fernando)','Active', ''),
    (14, 'Benchtop Injector','Edwards RV8', 'Fomblin', 'Process (Jack)','Active', ''),
    (15, '46/14 injector', 'Edwards RV8', 'Ultra Grade 19', 'Process (Jack)', 'Active',''),
    (16, 'Zeus', 'Edwards RV8', 'Fomblin', 'Chem (Elena)', 'Active',''),
    (17, 'P&P Station 0040','Edwards RV8', 'Fomblin', 'Chem (Elena)', 'Active',''),
    (18, 'P&P Station 0041', 'Edwards RV9', 'Fomblin', 'Chem (Elena)', 'Active',''),
    (19, 'MCI Waste System', 'Edwards RV8', 'Ultra Grade 19', 'Process (Ben)', 'Active','S/N 109433259'),
    (20, 'Spare 1 0045', 'Edwards RV12', 'Ultra Grade 19', 'Jack','Active', 'S/N 21968-3/16/22, South 8 0045'),
    (21, 'Spare 2 30285-112724', 'Edwards RV8', 'Ultra Grade 19', 'Jack','Active', 'S/N 30285-112724'),
    (22, 'Spare 3 240537431', 'Edwards RV8', 'Ultra Grade 19', 'Jack','Active', 'S/N 240537431'),
    (23, 'Spare 4 28651-5824', 'Edwards RV12', 'Ultra Grade 19', 'Jack','Active', 'In cabinet in bench 7, S/N 28651-5824')
]

log_data = [
    (1, date(2025, 4, 3), '2025-WW14', True, True, True, 70.8, 'None Required', ''),
    (2, date(2025, 4, 3), '2025-WW14', True, True, True, 72.4, 'None Required', ''),
    (6, date(2025, 4, 3), '2025-WW14', True, True, True, 71.5, 'None Required', ''),
    (7, date(2025, 4, 3), '2025-WW14', True, True, True, 76.4, 'None Required', ''),
    (8, date(2025, 4, 3), '2025-WW14', True, True, True, 81.8, 'None Required', ''),
    (9, date(2025, 4, 3), '2025-WW14', True, True, True, 65.3, 'None Required', ''),
    (10, date(2025, 4, 3), '2025-WW14', True, True, True, 85.8, 'None Required', ''),
    (11, date(2025, 4, 3), '2025-WW14', True, True, True, 67.2, 'None Required', ''),
    (12, date(2025, 4, 3), '2025-WW14', True, False, False, 82.6, 'Drain & Replace Oil', 'Drained oil and replaced'),
    (13, date(2025, 4, 3), '2025-WW14', False, True, True, 77.3, 'Add Oil', 'Added Ultra 19 oil'),
    (14, date(2025, 4, 3), '2025-WW14', False, True, True, 69.2, 'Add Oil', 'Added half a container'),
    (15, date(2025, 4, 3), '2025-WW14', True, True, True, 75.8, 'None Required', ''),
    (16, date(2025, 4, 3), '2025-WW14', True, True, True, 85.9, 'None Required', ''),
    (17, date(2025, 4, 3), '2025-WW14', True, True, True, 85.0, 'None Required', ''),
    (18, date(2025, 4, 3), '2025-WW14', True, True, True, 79.4, 'None Required', ''),
    (19, date(2025, 4, 3), '2025-WW14', False, False, False, None, 'None Required', 'Pump not operating'),
    (23, date(2025, 4, 3), '2025-WW14', True, True, False, None, 'None Required', ''),
    (9, date(2025, 4, 8), '2025-WW15', False, False, True, None, 'Add Oil', 'Completely out of oil')
]

def initialize_database():
    try:
        with app.app_context():
            db.create_all()

            MaintenanceLog.query.delete()
            Equipment.query.delete()
            db.session.commit()
            logger.info("Existing data cleared successfully.")

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

            equipment_map = {e.equipment_id: e.equipment_id for e in Equipment.query.all()}

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
            logger.info('✅ Equipment and maintenance log data loaded successfully.')
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    initialize_database()