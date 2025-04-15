# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
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
app.config['SECRET_KEY'] = 'yoshi_boy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SIMPLIFIED DATABASE CONFIGURATION
# Always use a database in the current directory for simplicity
db_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(db_dir, "vacuum_pump_maintenance.db")

# Log the database path
print(f"Using database at: {db_path}")
logger.info(f"Using database at: {db_path}")

# Set the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db = SQLAlchemy(app)

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
    return redirect(url_for('dashboard'))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/db-status')
def db_status():
    """Check database status and content"""
    try:
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI']

        # Count records in tables
        equipment_count = Equipment.query.count()
        logs_count = MaintenanceLog.query.count()

        # Get sample data
        equipment_sample = [{
            'id': e.equipment_id,
            'name': e.equipment_name,
            'pump_model': e.pump_model,
            'oil_type': e.oil_type,
            'pump_owner': e.pump_owner,
            'status': e.status,
            'notes': e.notes
        } for e in Equipment.query.limit(3).all()]

        logs_sample = [{
            'id': log.log_id,
            'equipment_id': log.equipment_id,
            'work_week': log.work_week,
            'check_date': log.check_date.strftime('%Y-%m-%d') if log.check_date else None,
            'pump_temp': log.pump_temp
        } for log in MaintenanceLog.query.limit(3).all()]

        return jsonify({
            "status": "success",
            "database_path": db_path,
            "equipment_count": equipment_count,
            "logs_count": logs_count,
            "equipment_sample": equipment_sample,
            "logs_sample": logs_sample,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

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

@app.route('/init-db')
def init_db_route():
    """Initialize the database with sample data"""
    try:
        # Import here to avoid circular imports
        from render_init_db import create_sample_data
        create_sample_data()
        return jsonify({
            "status": "success",
            "message": "Database initialized with sample data",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/direct-init-db')
def direct_init_db_route():
    """Initialize the database directly with SQLite"""
    try:
        import subprocess
        result = subprocess.run(['python', 'direct_db_init.py'], capture_output=True, text=True)
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

@app.route('/emergency-db-init')
def emergency_db_init():
    """Emergency database initialization using seed_initial_data.py"""
    try:
        # Import the initialization function from seed_initial_data.py
        from seed_initial_data import initialize_database

        # Run the initialization function
        initialize_database()

        # Return success response
        return jsonify({
            "status": "success",
            "message": "Database initialized successfully using seed_initial_data.py",
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
def equipment_list():
    try:
        equipment = Equipment.query.order_by(Equipment.equipment_id).all()
        return render_template('equipment_list.html', equipment=equipment)
    except Exception as e:
        logger.error(f"Error in equipment_list: {e}")
        flash(f"An error occurred while loading equipment list.", "danger")
        return render_template('error.html', error=str(e)), 500

@app.route('/equipment/<int:equipment_id>')
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
        # Get all pump owners
        pump_owners = db.session.query(Equipment.pump_owner).distinct().all()
        pump_owners = [owner[0] for owner in pump_owners if owner[0] is not None and owner[0].strip() != '']

        # Calculate scores for each pump owner
        hall_of_fame = []
        for owner in pump_owners:
            # Count equipment owned by this owner
            owned_equipment_count = Equipment.query.filter(Equipment.pump_owner == owner).count()
            if owned_equipment_count == 0:
                continue

            # Get all maintenance logs by this owner
            owner_logs = MaintenanceLog.query.join(Equipment).filter(
                MaintenanceLog.user_name == owner
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