# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import sqlite3
import os
import json
import logging
import sys
import shutil
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'yoshi_boy')  # Use environment variable for security
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts for 7 days

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import Supabase configuration
from supabase_config import get_db_connection_string

# DATABASE CONFIGURATION
print("Configuring database connection...")
logger.info("Configuring database connection...")

try:
    # Try to get Supabase connection string
    supabase_db_url = get_db_connection_string()

    if supabase_db_url:
        # Use Supabase PostgreSQL database
        app.config['SQLALCHEMY_DATABASE_URI'] = supabase_db_url
        logger.info(f"Using Supabase PostgreSQL database")
        print(f"Using Supabase PostgreSQL database")
    elif os.environ.get('DATABASE_URL'):
        # Fallback to Render PostgreSQL database URL if available
        database_url = os.environ.get('DATABASE_URL')
        # Render uses postgres:// but SQLAlchemy requires postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        # Set the database URI to the PostgreSQL URL
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        logger.info(f"Using Render PostgreSQL database")
        print(f"Using Render PostgreSQL database")
    else:
        # Local development - use SQLite
        db_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(db_dir, "vacuum_pump_maintenance.db")

        # Log the database path
        print(f"Using SQLite database at: {db_path}")
        logger.info(f"Using SQLite database at: {db_path}")

        # Set the database URI to SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # Enable SQLAlchemy echo for debugging
    app.config['SQLALCHEMY_ECHO'] = os.environ.get('SQLALCHEMY_ECHO', 'false').lower() == 'true'

    # Set connection pool options - different for PostgreSQL and SQLite
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        # PostgreSQL-specific options
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_timeout': 60,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'vacuum_pump_maintenance'
            }
        }
    else:
        # SQLite-specific options
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True
        }

    # Disable track modifications to improve performance
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Log the database connection details
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    masked_url = db_url
    if '@' in db_url:
        # Mask the password in the URL for logging
        parts = db_url.split('@')
        auth_parts = parts[0].split(':')
        if len(auth_parts) >= 3:
            masked_url = f"{auth_parts[0]}:{auth_parts[1]}:****@{parts[1]}"

    logger.info(f"Database URL: {masked_url}")

except Exception as e:
    logger.error(f"Error configuring database: {e}")
    print(f"Error configuring database: {e}")

db = SQLAlchemy(app)

# Initialize authentication
from auth import setup_auth
login_manager = setup_auth(app)

def get_work_week(date_obj=None):
    """Calculate the work week in YYYY-WW format."""
    if date_obj is None:
        date_obj = datetime.now()
    year = date_obj.year
    week = date_obj.isocalendar()[1]
    return f"{year}-WW{week:02d}"

def parse_temperature(temp_str):
    """Parse temperature string to float with error handling."""
    if not temp_str or temp_str.strip() == '':
        return None
    try:
        return float(temp_str)
    except ValueError:
        return None

class Equipment(db.Model):
    equipment_id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    pump_model = db.Column(db.String(100))
    oil_type = db.Column(db.String(100))
    pump_owner = db.Column(db.String(100))
    status = db.Column(db.String(50), default='active')
    notes = db.Column(db.Text)

    maintenance_logs = db.relationship('MaintenanceLog', backref='equipment', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Equipment({self.equipment_id}: {self.equipment_name})"

    def to_dict(self):
        """Convert equipment object to dictionary"""
        return {
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment_name,
            'pump_model': self.pump_model,
            'oil_type': self.oil_type,
            'pump_owner': self.pump_owner,
            'status': self.status,
            'notes': self.notes
        }

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

@app.route('/')
def index():
    # If user is authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Otherwise show login page
    return render_template('login.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db_ok = False
        error_msg = None
        try:
            # Try to execute a simple query
            db.session.execute('SELECT 1').scalar()
            db_ok = True
        except Exception as e:
            error_msg = str(e)

        # Get environment info
        env_info = {
            'DATABASE_URL': 'Present' if os.environ.get('DATABASE_URL') else 'Missing',
            'RENDER': os.environ.get('RENDER'),
            'SQLALCHEMY_DATABASE_URI': app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set').split('@')[0] + '@...' if '@' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set'),
            'SQLALCHEMY_ECHO': app.config.get('SQLALCHEMY_ECHO', False)
        }

        return jsonify({
            "status": "healthy",
            "database_ok": db_ok,
            "database_error": error_msg,
            "environment": env_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Removed duplicate db_status route - using the more detailed version below

@app.route('/run-seed-script')
def run_seed_script():
    """Run the seed_initial_data.py script directly"""
    try:
        import subprocess
        result = subprocess.run(['python', 'seed_initial_data.py'], capture_output=True, text=True)

        return jsonify({
            "status": "success" if result.returncode == 0 else "error",
            "message": "Seed script executed",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def is_database_initialized():
    """Check if the database has been initialized by looking for tables"""
    try:
        # Check if the Equipment table exists and has data
        equipment_count = db.session.query(db.func.count(Equipment.equipment_id)).scalar()
        return equipment_count > 0
    except Exception as e:
        logger.error(f"Error checking database initialization: {e}")
        return False

@app.route('/init-db')
def init_db_route():
    """Initialize the database with sample data only if not already initialized"""
    try:
        # Get database connection information
        db_info = {
            "database_type": "PostgreSQL" if "postgresql" in app.config['SQLALCHEMY_DATABASE_URI'] else "SQLite",
            "connection": app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0] + '@...' if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else app.config['SQLALCHEMY_DATABASE_URI']
        }

        # Check if database is already initialized
        try:
            equipment_count = Equipment.query.count()
            if equipment_count > 0:
                return jsonify({
                    "status": "success",
                    "message": f"Database already contains {equipment_count} equipment items. No action taken.",
                    "database_info": db_info,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as db_error:
            # If we get an error, it might be because tables don't exist yet
            logger.warning(f"Error checking database: {db_error}. Will attempt to create tables.")

        # Create tables first
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as table_error:
            return jsonify({
                "status": "error",
                "message": f"Failed to create database tables: {table_error}",
                "database_info": db_info,
                "timestamp": datetime.now().isoformat()
            }), 500

        # Now import and run the initialization function
        try:
            from db_init import create_sample_data
            create_sample_data()

            # Verify initialization was successful
            equipment_count = Equipment.query.count()
            return jsonify({
                "status": "success",
                "message": f"Database initialized successfully with {equipment_count} equipment items",
                "database_info": db_info,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as init_error:
            return jsonify({
                "status": "error",
                "message": f"Failed to initialize database with sample data: {init_error}",
                "database_info": db_info,
                "timestamp": datetime.now().isoformat()
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error during database initialization: {e}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/direct-init-db')
def direct_init_db_route():
    """Initialize the database directly"""
    try:
        # Check if database is already initialized
        if is_database_initialized():
            return jsonify({
                "status": "success",
                "message": "Database already initialized with data. No action taken.",
                "timestamp": datetime.now().isoformat()
            })

        import subprocess
        result = subprocess.run(['python', 'db_init.py'], capture_output=True, text=True)
        return jsonify({
            "status": "success" if result.returncode == 0 else "error",
            "message": "Database directly initialized with sample data",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/backup-db')
def backup_db_route():
    """Create a backup of the database"""
    try:
        from db_backup import backup_database
        result = backup_database()

        if result['status'] == 'success':
            return jsonify({
                "status": "success",
                "message": f"Database backup created successfully with {result['equipment_count']} equipment records and {result['logs_count']} maintenance logs",
                "file": result['file'],
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to create database backup: {result['message']}",
                "timestamp": datetime.now().isoformat()
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error creating database backup: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/list-backups')
def list_backups_route():
    """List all available database backups"""
    try:
        import os
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

        if not os.path.exists(backup_dir):
            return jsonify({
                "status": "success",
                "message": "No backups found",
                "backups": [],
                "timestamp": datetime.now().isoformat()
            })

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('db_backup_') and filename.endswith('.json'):
                file_path = os.path.join(backup_dir, filename)
                backups.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })

        # Sort backups by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)

        return jsonify({
            "status": "success",
            "message": f"Found {len(backups)} backups",
            "backups": backups,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error listing backups: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/restore-db/<filename>')
def restore_db_route(filename):
    """Restore database from a backup file"""
    try:
        import os
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        backup_file = os.path.join(backup_dir, filename)

        if not os.path.exists(backup_file):
            return jsonify({
                "status": "error",
                "message": f"Backup file not found: {filename}",
                "timestamp": datetime.now().isoformat()
            }), 404

        # Create a backup before restoring
        from db_backup import backup_database
        backup_result = backup_database()

        if backup_result['status'] == 'success':
            logger.info(f"Created safety backup before restore: {backup_result['file']}")
        else:
            logger.warning(f"Failed to create safety backup before restore: {backup_result.get('message')}")

        # Restore from backup
        from db_backup import restore_database
        result = restore_database(backup_file)

        if result['status'] == 'success':
            return jsonify({
                "status": "success",
                "message": f"Database restored successfully with {result['equipment_count']} equipment records and {result['logs_count']} maintenance logs",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to restore database: {result['message']}",
                "timestamp": datetime.now().isoformat()
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error restoring database: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# Schedule automatic backups
def setup_scheduled_tasks():
    """Set up scheduled tasks that run in the background"""
    try:
        import threading
        import time

        def scheduled_backup():
            """Run a database backup every day"""
            while True:
                try:
                    # Sleep for 24 hours
                    time.sleep(24 * 60 * 60)

                    # Run backup
                    from db_backup import backup_database
                    result = backup_database()

                    if result['status'] == 'success':
                        logger.info(f"Scheduled backup created successfully: {result['file']}")
                    else:
                        logger.error(f"Scheduled backup failed: {result.get('message')}")

                    # Clean up old backups (keep only the 10 most recent)
                    import os
                    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
                    if os.path.exists(backup_dir):
                        backups = []
                        for filename in os.listdir(backup_dir):
                            if filename.startswith('db_backup_') and filename.endswith('.json'):
                                file_path = os.path.join(backup_dir, filename)
                                backups.append({
                                    "filename": filename,
                                    "path": file_path,
                                    "created": os.path.getctime(file_path)
                                })

                        # Sort backups by creation time (newest first)
                        backups.sort(key=lambda x: x['created'], reverse=True)

                        # Delete old backups
                        for backup in backups[10:]:
                            try:
                                os.remove(backup['path'])
                                logger.info(f"Deleted old backup: {backup['filename']}")
                            except Exception as e:
                                logger.error(f"Error deleting old backup {backup['filename']}: {e}")
                except Exception as e:
                    logger.error(f"Error in scheduled backup: {e}")

        # Start the backup thread
        backup_thread = threading.Thread(target=scheduled_backup, daemon=True)
        backup_thread.start()
        logger.info("Scheduled backup thread started")
    except Exception as e:
        logger.error(f"Error setting up scheduled tasks: {e}")

# Create a function to initialize the app
def init_app(app):
    """Initialize the application"""
    # Set up scheduled tasks
    setup_scheduled_tasks()

# Register the init_app function with Flask 2.0+ using the new approach
with app.app_context():
    init_app(app)

@app.route('/emergency-db-init')
def emergency_db_init():
    """Emergency database initialization"""
    try:
        # Check if database is already initialized
        if is_database_initialized():
            return jsonify({
                "status": "success",
                "message": "Database already initialized with data. No action taken.",
                "timestamp": datetime.now().isoformat()
            })

        # Import the initialization function
        from db_init import create_sample_data

        # Run the initialization function
        create_sample_data()

        # Return success response
        return jsonify({
            "status": "success",
            "message": "Database initialized successfully",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": str(sys.exc_info()),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/db-status')
def db_status():
    """Check database status and return information about tables and records"""
    try:
        # Get database connection information
        db_info = {
            "database_type": "PostgreSQL" if "postgresql" in app.config['SQLALCHEMY_DATABASE_URI'] else "SQLite",
            "connection": app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0] + '@...' if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else app.config['SQLALCHEMY_DATABASE_URI'],
            "tables": {}
        }

        # Get table information
        equipment_count = Equipment.query.count()
        db_info["tables"]["equipment"] = {
            "count": equipment_count,
            "sample": [e.to_dict() for e in Equipment.query.limit(3).all()] if equipment_count > 0 else []
        }

        maintenance_count = MaintenanceLog.query.count()
        db_info["tables"]["maintenance_logs"] = {
            "count": maintenance_count,
            "sample": [{
                "log_id": log.log_id,
                "equipment_id": log.equipment_id,
                "check_date": log.check_date.strftime('%Y-%m-%d') if log.check_date else None,
                "user_name": log.user_name,
                "service": log.service
            } for log in MaintenanceLog.query.limit(3).all()] if maintenance_count > 0 else []
        }

        # Add information about seed_initial_data.py
        try:
            from seed_initial_data import equipment_data, log_data
            db_info["seed_data"] = {
                "equipment_count": len(equipment_data),
                "log_count": len(log_data)
            }
        except Exception as e:
            db_info["seed_data"] = {
                "error": str(e)
            }

        return jsonify({
            "status": "success",
            "message": "Database status retrieved successfully",
            "data": db_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": str(sys.exc_info()),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        today = datetime.now()
        current_work_week = get_work_week(today)

        equipment_needs_oil = db.session.query(Equipment).join(MaintenanceLog).filter(
            MaintenanceLog.service.in_(['Add Oil', 'Drain & Replace Oil']),
            MaintenanceLog.check_date >= (today - timedelta(days=14))
        ).all()

        equipment_high_temp = db.session.query(Equipment).join(MaintenanceLog).filter(
            MaintenanceLog.pump_temp >= 80,
            MaintenanceLog.check_date >= (today - timedelta(days=14))
        ).all()

        current_logs = MaintenanceLog.query.filter(
            MaintenanceLog.work_week == current_work_week
        ).order_by(MaintenanceLog.equipment_id).all()

        equipment_count = Equipment.query.count()
        maintained_count = db.session.query(Equipment).join(MaintenanceLog).filter(
            MaintenanceLog.check_date >= (today - timedelta(days=7))
        ).distinct().count()
        maintenance_rate = (maintained_count / equipment_count * 100) if equipment_count > 0 else 0

        return render_template(
            'dashboard.html',
            equipment_needs_oil=equipment_needs_oil,
            equipment_high_temp=equipment_high_temp,
            current_logs=current_logs,
            maintenance_rate=maintenance_rate,
            current_work_week=current_work_week
        )
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        flash(f"An error occurred while loading the dashboard. Please try again.", "danger")
        return render_template('error.html', error=str(e)), 500

@app.route('/equipment')
@login_required
def equipment_list():
    try:
        equipment = Equipment.query.order_by(Equipment.equipment_id).all()
        return render_template('equipment_list.html', equipment=equipment)
    except Exception as e:
        logger.error(f"Error in equipment_list: {e}")
        flash(f"An error occurred while loading equipment list.", "danger")
        return render_template('error.html', error=str(e)), 500

@app.route('/equipment/<int:equipment_id>')
@login_required
def equipment_detail(equipment_id):
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        maintenance_logs = MaintenanceLog.query.filter_by(equipment_id=equipment_id).order_by(MaintenanceLog.check_date.desc()).all()
        return render_template('equipment_detail.html', equipment=equipment, logs=maintenance_logs)
    except Exception as e:
        logger.error(f"Error in equipment_detail for ID {equipment_id}: {e}")
        flash(f"An error occurred while loading equipment details.", "danger")
        return redirect(url_for('equipment_list'))

@app.route('/equipment/add', methods=['GET', 'POST'])
@login_required
def equipment_add():
    if request.method == 'POST':
        try:
            equipment_id = request.form.get('equipment_id')

            existing_equipment = Equipment.query.filter_by(equipment_id=equipment_id).first()
            if existing_equipment:
                flash(f'Equipment {equipment_id} already exists. Please use a different number.', 'warning')
                return redirect(url_for('equipment_add'))

            new_equipment = Equipment(
                equipment_id=equipment_id,
                equipment_name=request.form.get('equipment_name'),
                pump_model=request.form.get('pump_model'),
                oil_type=request.form.get('oil_type'),
                pump_owner=request.form.get('pump_owner'),
                status=request.form.get('status', 'active'),
                notes=request.form.get('notes')
            )

            db.session.add(new_equipment)
            db.session.commit()
            flash('Equipment added successfully', 'success')
            return redirect(url_for('equipment_list'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding equipment: {e}")
            flash(f'Error adding equipment: {str(e)}', 'danger')
            return redirect(url_for('equipment_add'))

    try:
        last_equipment = Equipment.query.order_by(Equipment.equipment_id.desc()).first()
        next_equipment_id = 1
        if last_equipment:
            next_equipment_id = last_equipment.equipment_id + 1

        return render_template('equipment_form.html', next_equipment_id=next_equipment_id)
    except Exception as e:
        logger.error(f"Error loading equipment add form: {e}")
        flash(f'Error loading form: {str(e)}', 'danger')
        return redirect(url_for('equipment_list'))

@app.route('/weekly-log', methods=['GET', 'POST'])
@login_required
def weekly_log():
    try:
        today = datetime.now()
        current_work_week = get_work_week(today)

        work_week = request.args.get('work_week', current_work_week)

        # Check if we need to reset the weekly log
        # If the requested work week is the current week, check if we need to reset
        if work_week == current_work_week:
            # Get the most recent log for this week
            most_recent_log = MaintenanceLog.query.filter_by(work_week=work_week).order_by(MaintenanceLog.check_date.desc()).first()

            # If there's a log and it's from a previous week, we should reset
            if most_recent_log and most_recent_log.check_date.isocalendar()[1] != today.isocalendar()[1]:
                # Delete all logs for this week to reset
                logs_to_delete = MaintenanceLog.query.filter_by(work_week=work_week).all()
                for log in logs_to_delete:
                    db.session.delete(log)
                db.session.commit()
                flash(f"Weekly log has been reset for {work_week}", "info")

        # Get all equipment first to count how many are filtered out
        all_equipment = Equipment.query.order_by(Equipment.equipment_id).all()

        # Filter out equipment with "scroll" in oil_type or "spare" in equipment_name
        equipment_list = Equipment.query.filter(
            # For oil_type, handle NULL values and exclude "scroll" (case insensitive)
            (Equipment.oil_type.is_(None) | ~Equipment.oil_type.ilike('%scroll%')),
            # Exclude equipment with "spare" in name (case insensitive)
            ~Equipment.equipment_name.ilike('%spare%')
        ).order_by(Equipment.equipment_id).all()

        # Calculate how many items were filtered out
        filtered_out_count = len(all_equipment) - len(equipment_list)
        if filtered_out_count > 0:
            logger.info(f"Filtered out {filtered_out_count} equipment items with 'scroll' in oil type or 'spare' in name")

        existing_logs = {}
        logs = MaintenanceLog.query.filter_by(work_week=work_week).all()
        for log in logs:
            existing_logs[log.equipment_id] = log

        current_user_name = ''
        if logs:
            current_user_name = logs[0].user_name or ''

        if request.method == 'POST':
            try:
                check_date_str = request.form.get('check_date')
                try:
                    check_date = datetime.strptime(check_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash(f"Invalid date format: {check_date_str}. Please use YYYY-MM-DD format.", "danger")
                    return redirect(url_for('weekly_log', work_week=work_week))

                user_name = request.form.get('user_name', '')

                for equipment in equipment_list:
                    log = existing_logs.get(equipment.equipment_id)
                    if not log:
                        log = MaintenanceLog(
                            equipment_id=equipment.equipment_id,
                            work_week=work_week,
                            check_date=check_date,
                            user_name=user_name,
                        )
                        db.session.add(log)
                    else:
                        log.user_name = user_name
                        log.check_date = check_date

                    equipment_key = f"equipment_{equipment.equipment_id}"
                    log.oil_level_ok = equipment_key + "_oil_level_ok" in request.form
                    log.oil_condition_ok = equipment_key + "_oil_condition_ok" in request.form
                    log.oil_filter_ok = equipment_key + "_oil_filter_ok" in request.form

                    temp_value = request.form.get(equipment_key + "_pump_temp")
                    log.pump_temp = parse_temperature(temp_value)

                    log.service = request.form.get(equipment_key + "_service", 'None Required')
                    log.service_notes = request.form.get(equipment_key + "_service_notes", '')

                db.session.commit()
                flash('Weekly maintenance log saved successfully', 'success')
                return redirect(url_for('weekly_log', work_week=work_week))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving weekly log: {e}")
                flash(f"Error saving weekly log: {str(e)}", "danger")

        return render_template(
            'weekly_log.html',
            equipment_list=equipment_list,
            work_week=work_week,
            existing_logs=existing_logs,
            current_date=today.strftime('%Y-%m-%d'),
            current_user_name=current_user_name
        )
    except Exception as e:
        logger.error(f"Error in weekly_log: {e}")
        flash(f"An error occurred while loading weekly log form: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

@app.route('/maintenance/logs')
@login_required
def maintenance_logs():
    try:
        work_week = request.args.get('work_week', '')
        equipment_id = request.args.get('equipment_id', '')

        query = MaintenanceLog.query

        if work_week:
            query = query.filter(MaintenanceLog.work_week == work_week)

        if equipment_id:
            try:
                equipment_id = int(equipment_id)
                query = query.filter(MaintenanceLog.equipment_id == equipment_id)
            except ValueError:
                pass

        logs = query.order_by(MaintenanceLog.check_date.desc(), MaintenanceLog.equipment_id).all()

        work_weeks = db.session.query(MaintenanceLog.work_week).distinct().order_by(MaintenanceLog.work_week.desc()).all()
        work_weeks = [ww[0] for ww in work_weeks if ww[0]]

        equipment_list = Equipment.query.order_by(Equipment.equipment_id).all()

        equipment_logs = {}
        for log in logs:
            equipment_logs[log.equipment_id] = log

        return render_template(
            'maintenance_logs.html',
            logs=logs,
            work_weeks=work_weeks,
            equipment_list=equipment_list,
            equipment_logs=equipment_logs,
            selected_work_week=work_week,
            selected_equipment_id=equipment_id
        )
    except Exception as e:
        logger.error(f"Error in maintenance_logs: {e}")
        flash(f"An error occurred while loading maintenance logs: {str(e)}", "danger")
        return redirect(url_for('dashboard'))


@app.route('/maintenance/log/<int:log_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_maintenance_log(log_id):
    try:
        log = MaintenanceLog.query.get_or_404(log_id)

        if request.method == 'POST':
            try:
                log.oil_level_ok = 'oil_level_ok' in request.form
                log.oil_condition_ok = 'oil_condition_ok' in request.form
                log.oil_filter_ok = 'oil_filter_ok' in request.form

                temp_value = request.form.get('pump_temp')
                log.pump_temp = parse_temperature(temp_value)

                # Handle custom service option
                service = request.form.get('service', 'None Required')
                if service == 'custom':
                    # Get the custom service value from a hidden field or prompt
                    custom_service = request.form.get('custom_service', '')
                    if custom_service and custom_service.strip() != '':
                        service = custom_service
                    else:
                        service = 'None Required'

                log.service = service
                log.service_notes = request.form.get('service_notes')
                log.user_name = request.form.get('user_name')

                # We don't allow changing the check date
                # The check_date field is readonly in the form

                db.session.commit()
                flash('Maintenance log updated successfully', 'success')
                return redirect(url_for('maintenance_logs'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating maintenance log {log_id}: {e}")
                flash(f"Error updating maintenance log: {str(e)}", "danger")

        return render_template('edit_maintenance_log.html', log=log)
    except Exception as e:
        logger.error(f"Error in edit_maintenance_log for ID {log_id}: {e}")
        flash(f"An error occurred while loading log {log_id} for editing: {str(e)}", "danger")
        return redirect(url_for('maintenance_logs'))

@app.route('/maintenance/log/<int:log_id>/delete')
@login_required
def delete_maintenance_log(log_id):
    try:
        log = MaintenanceLog.query.get_or_404(log_id)
        db.session.delete(log)
        db.session.commit()
        flash('Maintenance log deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting maintenance log {log_id}: {e}")
        flash(f"Error deleting maintenance log: {str(e)}", "danger")

    return redirect(request.referrer or url_for('weekly_log'))

@app.route('/equipment/delete-multiple', methods=['POST'])
@login_required
def equipment_delete_multiple():
    equipment_ids = request.form.getlist('equipment_ids')

    if not equipment_ids:
        flash('No equipment selected for deletion', 'warning')
        return redirect(url_for('equipment_list'))

    try:
        deleted_count = 0
        for eq_id in equipment_ids:
            equipment = Equipment.query.get(eq_id)
            if equipment:
                db.session.delete(equipment)
                deleted_count += 1

        db.session.commit()
        flash(f'Successfully deleted {deleted_count} equipment items', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in equipment_delete_multiple: {e}")
        flash(f'Error deleting equipment: {str(e)}', 'danger')

    return redirect(url_for('equipment_list'))

@app.route('/api/dropdown-options/<field>')
def dropdown_options(field):
    """Get unique values for dropdown fields from existing records"""
    valid_fields = ['pump_model', 'oil_type', 'pump_owner', 'service', 'user_name']

    if field not in valid_fields:
        return jsonify([])

    try:
        if field in ['pump_model', 'oil_type', 'pump_owner']:
            values = db.session.query(getattr(Equipment, field)).distinct().all()
            values = [val[0] for val in values if val[0] is not None]
        elif field == 'service':
            # Get standard service options plus any custom ones from the database
            standard_options = [
                'None Required', 'Add Oil', 'Drain & Replace Oil',
                'Swap Pump for Spare', 'Drain Oil Filter', "Other (see 'Service Notes')"
            ]
            custom_values = db.session.query(MaintenanceLog.service).distinct().all()
            custom_values = [val[0] for val in custom_values if val[0] is not None
                            and val[0] not in standard_options]
            values = standard_options + custom_values
        elif field == 'user_name':
            # Get unique user names from maintenance logs
            user_values = db.session.query(MaintenanceLog.user_name).distinct().all()
            user_values = [val[0] for val in user_values if val[0] is not None and val[0].strip() != '']

            # Also include pump owners as potential employees
            owner_values = db.session.query(Equipment.pump_owner).distinct().all()
            owner_values = [val[0] for val in owner_values if val[0] is not None and val[0].strip() != '']

            # Combine and remove duplicates
            values = list(set(user_values + owner_values))

        values.sort()
        return jsonify(values)
    except Exception as e:
        logger.error(f"Error getting dropdown options for {field}: {e}")
        return jsonify([])

@app.route('/equipment/<int:equipment_id>/edit', methods=['GET', 'POST'])
@login_required
def equipment_edit(equipment_id):
    try:
        equipment = Equipment.query.get_or_404(equipment_id)

        if request.method == 'POST':
            try:
                equipment.equipment_name = request.form.get('equipment_name')
                equipment.pump_model = request.form.get('pump_model')
                equipment.oil_type = request.form.get('oil_type')
                equipment.pump_owner = request.form.get('pump_owner')
                equipment.status = request.form.get('status')
                equipment.notes = request.form.get('notes')

                db.session.commit()
                flash('Equipment updated successfully', 'success')
                return redirect(url_for('equipment_detail', equipment_id=equipment.equipment_id))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating equipment {equipment_id}: {e}")
                flash(f"Error updating equipment: {str(e)}", "danger")

        return render_template('edit_equipment_form.html', equipment=equipment)
    except Exception as e:
        logger.error(f"Error in equipment_edit for ID {equipment_id}: {e}")
        flash(f"An error occurred while editing equipment: {str(e)}", "danger")
        return redirect(url_for('equipment_list'))

@app.route('/save_equipment_log/<int:equipment_id>/<work_week>', methods=['POST'])
@login_required
def save_equipment_log(equipment_id, work_week):
    try:
        equipment = Equipment.query.get_or_404(equipment_id)

        existing_log = MaintenanceLog.query.filter_by(
            equipment_id=equipment_id,
            work_week=work_week
        ).first()

        # Use the hidden or visible check_date field
        check_date_str = request.form.get('check_date')
        if not check_date_str or check_date_str.strip() == '':
            check_date_str = request.form.get('check_date_hidden')

        try:
            check_date = datetime.strptime(check_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash(f"Invalid date format: {check_date_str}. Please use YYYY-MM-DD format.", "danger")
            return redirect(url_for('weekly_log', work_week=work_week))

        # Get user_name from form, or use pump_owner if this is a new log
        user_name = request.form.get('user_name', '')
        if not existing_log and (not user_name or user_name.strip() == ''):
            # Auto-fill with pump owner for first edit
            user_name = equipment.pump_owner if equipment.pump_owner else ''

        oil_level_ok = 'oil_level_ok' in request.form
        oil_condition_ok = 'oil_condition_ok' in request.form
        oil_filter_ok = 'oil_filter_ok' in request.form

        temp_value = request.form.get('pump_temp')
        pump_temp = parse_temperature(temp_value)

        # Handle custom service option
        service = request.form.get('service', 'None Required')
        if service == 'custom':
            # Get the custom service value from a hidden field or prompt
            custom_service = request.form.get('custom_service', '')
            if custom_service and custom_service.strip() != '':
                service = custom_service
            else:
                service = 'None Required'

        service_notes = request.form.get('service_notes', '')

        if existing_log:
            existing_log.check_date = check_date
            existing_log.user_name = user_name
            existing_log.oil_level_ok = oil_level_ok
            existing_log.oil_condition_ok = oil_condition_ok
            existing_log.oil_filter_ok = oil_filter_ok
            existing_log.pump_temp = pump_temp
            existing_log.service = service
            existing_log.service_notes = service_notes

            flash(f'Maintenance log for {equipment.equipment_name} updated successfully', 'success')
        else:
            new_log = MaintenanceLog(
                equipment_id=equipment_id,
                work_week=work_week,
                check_date=check_date,
                user_name=user_name,
                oil_level_ok=oil_level_ok,
                oil_condition_ok=oil_condition_ok,
                oil_filter_ok=oil_filter_ok,
                pump_temp=pump_temp,
                service=service,
                service_notes=service_notes
            )
            db.session.add(new_log)

            flash(f'Maintenance log for {equipment.equipment_name} created successfully', 'success')

        db.session.commit()

        # Update Hall of Fame scores when a maintenance log is saved
        try:
            # If the user is a pump owner, update their score
            if user_name and user_name.strip() != '':
                # Check if this user is a pump owner
                is_pump_owner = Equipment.query.filter(Equipment.pump_owner == user_name).first() is not None

                if is_pump_owner:
                    logger.info(f"Updating Hall of Fame score for pump owner: {user_name}")
                    # The Hall of Fame scores will be recalculated on the next dashboard view
                    # No need to do anything else here
        except Exception as e:
            logger.error(f"Error updating Hall of Fame score: {e}")
            # Don't let this error affect the main functionality
            pass

        return redirect(url_for('weekly_log', work_week=work_week))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving equipment log: {e}")
        flash(f"Error saving maintenance log: {str(e)}", "danger")
        return redirect(url_for('weekly_log', work_week=work_week))

@app.route('/api/chart-data')
def chart_data():
    try:
        logs = MaintenanceLog.query.join(Equipment).filter(
            MaintenanceLog.pump_temp.isnot(None),
            MaintenanceLog.check_date >= (datetime.now() - timedelta(days=60))
        ).order_by(MaintenanceLog.check_date).all()

        temp_data = {}
        dates = set()

        for log in logs:
            equipment_name = log.equipment.equipment_name
            date_str = log.check_date.strftime('%Y-%m-%d')
            dates.add(date_str)

            if equipment_name not in temp_data:
                temp_data[equipment_name] = {}

            temp_data[equipment_name][date_str] = log.pump_temp

        sorted_dates = sorted(list(dates))
        chart_data = {
            'labels': sorted_dates,
            'datasets': []
        }

        colors = [
            '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#6f42c1',
            '#5a5c69', '#858796', '#2e59d9', '#17a673', '#2c9faf', '#f8f9fc',
            '#e74a3b', '#fd7e14', '#f6c23e', '#20c9a6', '#28a745', '#6610f2',
            '#6f42c1', '#e83e8c', '#e74a3b', '#fd7e14', '#ffc107', '#28a745'
        ]

        for i, (equipment_name, temp_values) in enumerate(temp_data.items()):
            dataset = {
                'label': equipment_name,
                'data': [temp_values.get(date, None) for date in sorted_dates],
                'borderColor': colors[i % len(colors)],
                'backgroundColor': 'transparent',
                'pointRadius': 3
            }
            chart_data['datasets'].append(dataset)

        maintenance_counts = db.session.query(
            Equipment.equipment_name,
            db.func.count(MaintenanceLog.log_id)
        ).join(MaintenanceLog).group_by(Equipment.equipment_id).all()

        maintenance_data = {
            'labels': [item[0] for item in maintenance_counts],
            'datasets': [{
                'data': [item[1] for item in maintenance_counts],
                'backgroundColor': colors[:len(maintenance_counts)]
            }]
        }

        # Calculate Hall of Fame scores
        # Get all pump owners, excluding those who only own scroll pumps or spare equipment
        eligible_equipment = Equipment.query.filter(
            (Equipment.oil_type.is_(None) | ~Equipment.oil_type.ilike('%scroll%')),
            ~Equipment.equipment_name.ilike('%spare%')
        ).all()

        # Get unique eligible pump owners
        eligible_owners = set()
        for equip in eligible_equipment:
            if equip.pump_owner and equip.pump_owner.strip() != '':
                eligible_owners.add(equip.pump_owner)

        # Calculate scores for each eligible pump owner
        hall_of_fame = []
        for owner in eligible_owners:
            # Count eligible equipment owned by this owner (excluding scroll and spare)
            owned_equipment_count = Equipment.query.filter(
                Equipment.pump_owner == owner,
                (Equipment.oil_type.is_(None) | ~Equipment.oil_type.ilike('%scroll%')),
                ~Equipment.equipment_name.ilike('%spare%')
            ).count()

            if owned_equipment_count == 0:
                continue

            # Get all maintenance logs by this owner for eligible equipment only
            owner_logs = MaintenanceLog.query.join(Equipment).filter(
                MaintenanceLog.user_name == owner,
                (Equipment.oil_type.is_(None) | ~Equipment.oil_type.ilike('%scroll%')),
                ~Equipment.equipment_name.ilike('%spare%')
            ).all()

            # Group logs by week to calculate weekly scores
            weekly_scores = {}
            for log in owner_logs:
                week = log.work_week
                if week not in weekly_scores:
                    weekly_scores[week] = set()  # Use set to avoid counting the same equipment twice in a week
                weekly_scores[week].add(log.equipment_id)

            # Calculate total score: sum of (equipment maintained * 10 / equipment owned) for each week
            total_score = 0
            for week, equipment_ids in weekly_scores.items():
                weekly_score = len(equipment_ids) * 10 / owned_equipment_count
                total_score += weekly_score

            hall_of_fame.append({
                'name': owner,
                'score': round(total_score, 1),
                'equipment_owned': owned_equipment_count,
                'weeks_active': len(weekly_scores)
            })

        # Sort by score (highest first)
        hall_of_fame.sort(key=lambda x: x['score'], reverse=True)

        # Add rank
        for i, entry in enumerate(hall_of_fame):
            entry['rank'] = i + 1

        return jsonify({
            'temperature_chart': chart_data,
            'maintenance_chart': maintenance_data,
            'hall_of_fame': hall_of_fame
        })
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    flash(f"An error occurred: {str(error)}", "danger")
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found_error(error):
    flash("The requested page was not found.", "warning")
    return redirect(url_for('dashboard'))

# Only set SQLite pragmas when using SQLite
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
        cursor.close()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)