# --- Imports ---
import os
import sys
import uuid
from datetime import datetime, timedelta
import requests
import math
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import re
from werkzeug.middleware.proxy_fix import ProxyFix
import traceback
from sqlalchemy import desc
from typing import Any, cast

# --- Helper to select weather icon ---
def weather_icon(weather_str):
    if not weather_str:
        return "fas fa-question-circle text-muted"
    w = weather_str.lower()
    # Strip leading descriptor prefix like "clear sky:" if present
    if ':' in w:
        w = w.split(':', 1)[0].strip()
    if "sun" in w or "clear" in w:
        return "fas fa-sun text-warning"
    elif "cloud" in w:
        if "partly" in w or "some" in w:
            return "fas fa-cloud-sun text-info"
        else:
            return "fas fa-cloud text-secondary"
    elif "rain" in w or "shower" in w:
        return "fas fa-cloud-rain text-primary"
    elif "snow" in w:
        return "fas fa-snowflake text-light"
    elif "wind" in w:
        return "fas fa-wind text-info"
    else:
        return "fas fa-question-circle text-muted"


app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/tracker'
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SECRET_KEY'] = os.environ.get('TRACKER_SECRET_KEY', 'changeme-please-set-TRACKER_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TRACKER_DATABASE_URI', 'sqlite:///race_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# Secure/persistent session settings
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_SECURE'] = True

# Development toggles for hot reload
if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1':
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    try:
        app.jinja_env.auto_reload = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    except Exception:
        pass
    # Dev: local HTTP, so don't mark cookies as Secure and prefer http scheme
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_SECURE'] = False
    app.config['PREFERRED_URL_SCHEME'] = 'http'

def _is_dev_runtime() -> bool:
    return os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1'

@app.context_processor
def inject_env_flags():
    return {
        'is_dev': _is_dev_runtime()
    }


# --- Template context processor: asset_version for cache-busting ---
def _get_asset_version():
    try:
        # short git hash, fall back to timestamp
        import subprocess
        sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=os.path.dirname(__file__)).decode().strip()
        return sha
    except Exception:
        return str(int(datetime.utcnow().timestamp()))

@app.context_processor
def inject_asset_version():
    return {'asset_version': _get_asset_version()}

# --- Flask-Login Manager ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# --- PrefixMiddleware for subpath support ---
class PrefixMiddleware:
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        import sys
        configured_root = app.config.get('APPLICATION_ROOT', '') or ''
        header_script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        script_name = header_script_name or configured_root or ''
        if script_name and not script_name.startswith('/'):
            script_name = '/' + script_name
        path_info = environ.get('PATH_INFO', '')
        print(f"[PrefixMiddleware] BEFORE: script_name: {script_name}, path_info: {path_info}", file=sys.stderr)
        
        # Set the script name for Flask URL building
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        
        print(f"[PrefixMiddleware] AFTER: SCRIPT_NAME: {environ.get('SCRIPT_NAME', '')}, PATH_INFO: {environ.get('PATH_INFO', '')}", file=sys.stderr)
        return self.app(environ, start_response)

# Apply the middleware
app.wsgi_app = PrefixMiddleware(app.wsgi_app)


# --- Ensure upload directory exists ---
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)
except PermissionError:
    # Directory might already exist with proper permissions from Dockerfile
    pass

# --- Database setup ---
db = SQLAlchemy(app)



# --- Models ---
class User(UserMixin, db.Model):
    def __init__(self, username=None, email=None, password_hash=None, first_name=None, last_name=None, is_admin=False, reset_token=None, reset_token_expiry=None, created_at=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        self.reset_token = reset_token
        self.reset_token_expiry = reset_token_expiry
        self.created_at = created_at or datetime.utcnow()
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)  # Optional, email is primary
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship to races
    races = db.relationship('Race', backref='runner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not isinstance(self.password_hash, str):
            return False
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate a password reset token"""
        import secrets
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        return (self.reset_token == token and 
                self.reset_token_expiry and 
                self.reset_token_expiry > datetime.utcnow())
    
    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None

    def __repr__(self):
        return f'<User {self.username}>'

class Race(db.Model):
    def __init__(self, user_id, race_name, race_type, race_date, race_time, finish_time, location=None, weather=None, start_weather=None, finish_weather=None, notes=None, race_page_url=None, created_at=None):
        self.user_id = user_id
        self.race_name = race_name
        self.race_type = race_type
        self.race_date = race_date
        self.race_time = race_time
        self.finish_time = finish_time
        self.location = location
        self.weather = weather
        self.start_weather = start_weather
        self.finish_weather = finish_weather
        self.notes = notes
        self.race_page_url = race_page_url
        self.created_at = created_at or datetime.utcnow()
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    race_name = db.Column(db.String(200), nullable=False)
    race_type = db.Column(db.String(50), nullable=False)  # '5K', '10K', 'Half Marathon', 'Marathon', 'Other'
    race_date = db.Column(db.Date, nullable=False)
    race_time = db.Column(db.String(8), nullable=True)  # Format: HH:MM or HH:MM:SS
    finish_time = db.Column(db.String(20), nullable=False)  # Format: HH:MM:SS
    location = db.Column(db.String(200))
    weather = db.Column(db.String(100))  # legacy, can be removed later
    start_weather = db.Column(db.String(100))  # cached weather at start
    finish_weather = db.Column(db.String(100))  # cached weather at finish
    notes = db.Column(db.Text)
    race_page_url = db.Column(db.String(500))  # URL to race results page
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Photo relationships
    photos = db.relationship('RacePhoto', backref='race', lazy=True, cascade='all, delete-orphan')

    def time_to_seconds(self):
        """Convert finish time to seconds (float). Supports mm:ss.cc, mm:ss, hh:mm:ss(.cc), and 5K-only mm:ss:cc."""
        return _parse_duration_seconds(self.finish_time or '', (self.race_type or '').strip())

    def __repr__(self):
        return f'<Race {self.race_name} - {self.finish_time}>'

class RacePhoto(db.Model):
    def __init__(self, race_id, filename, original_filename, photo_type, caption=None):
        self.race_id = race_id
        self.filename = filename
        self.original_filename = original_filename
        self.photo_type = photo_type
        self.caption = caption
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    photo_type = db.Column(db.String(50), nullable=False)  # 'finish', 'medal', 'bib', 'other'
    caption = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RacePhoto {self.filename}>'

class Workout(db.Model):
    """Training workout model - different from formal races"""
    def __init__(self, user_id, workout_type, duration, distance=None, pace=None, calories=None, 
                 heart_rate_avg=None, heart_rate_max=None, notes=None, location=None, 
                 weather=None, workout_date=None, created_at=None):
        self.user_id = user_id
        self.workout_type = workout_type
        self.duration = duration
        self.distance = distance
        self.pace = pace
        self.calories = calories
        self.heart_rate_avg = heart_rate_avg
        self.heart_rate_max = heart_rate_max
        self.notes = notes
        self.location = location
        self.weather = weather
        self.workout_date = workout_date or datetime.utcnow().date()
        self.created_at = created_at or datetime.utcnow()
        
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    workout_type = db.Column(db.String(50), nullable=False)  # 'Running', 'Walking', 'Cycling', 'Other'
    duration = db.Column(db.String(20), nullable=False)  # Format: HH:MM:SS
    distance = db.Column(db.Float)  # Distance in miles/km
    pace = db.Column(db.String(10))  # Average pace per mile/km (MM:SS)
    calories = db.Column(db.Integer)  # Calories burned
    heart_rate_avg = db.Column(db.Integer)  # Average heart rate
    heart_rate_max = db.Column(db.Integer)  # Maximum heart rate
    notes = db.Column(db.Text)
    location = db.Column(db.String(200))
    weather = db.Column(db.String(100))
    workout_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('workouts', lazy=True, cascade='all, delete-orphan'))
    
    def duration_to_seconds(self):
        """Convert duration to seconds for calculations"""
        return _parse_duration_seconds(self.duration or '', 'workout')
    
    def calculate_pace(self):
        """Calculate pace if distance and duration are available"""
        if self.distance and self.duration:
            seconds = self.duration_to_seconds()
            if seconds > 0:
                pace_seconds = seconds / self.distance
                minutes = int(pace_seconds // 60)
                seconds = int(pace_seconds % 60)
                return f"{minutes:02d}:{seconds:02d}"
        return None
    
    def __repr__(self):
        return f'<Workout {self.workout_type} - {self.duration}>'

# --- Top-level function to add test races for a runner ---
def add_test_races(runner, race_types, locations):
    from random import choice, randint
    from datetime import datetime
    for i in range(10):
        race = Race(
            user_id=runner.id,
            race_name=f"Test Race {i+1}",
            race_type=choice(race_types),
            race_date=datetime(2024, randint(1,12), randint(1,28)).date(),
            race_time=f"0{randint(6,9)}:00",
            finish_time=f"{randint(20,59)}:{randint(10,59)}",
            location=choice(locations),
            weather="Sunny, 70°F, wind 5 mph",
            start_weather=None,
            finish_weather=None,
            notes=f"This is a test race entry number {i}."
        )
        db.session.add(race)
    db.session.commit()
    print("Test races added for runner.")

# --- Flask-Login user loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Admin Routes ---
@app.route('/admin')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    # Provide summary metrics expected by the template
    total_users = User.query.count()
    admin_users_count = User.query.filter_by(is_admin=True).count()
    total_races = Race.query.count()
    return render_template(
        'admin_users.html',
        users=users,
        total_users=total_users,
        admin_users=admin_users_count,
        total_races=total_races
    )

def reset_user_password(user, new_password):
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset for {user.email}')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/reset_password', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    """Admin-only: reset a user's password to a specified value."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot reset your own password from admin panel')
        return redirect(url_for('admin_users'))

    # Get the new password from the form
    new_password = request.form.get('new_password')
    if not new_password:
        flash('Password is required', 'danger')
        return redirect(url_for('admin_users'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'danger')
        return redirect(url_for('admin_users'))

    user.set_password(new_password)
    try:
        # Clear any outstanding reset token
        if hasattr(user, 'clear_reset_token'):
            user.clear_reset_token()
        db.session.commit()
        flash(f'Password successfully reset for {user.email}')
    except Exception:
        db.session.rollback()
        flash('Failed to reset password due to a server error.', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
def admin_toggle_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot modify your own admin status')
        return redirect(url_for('admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin privileges {status} for {user.email}')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot delete your own account')
        return redirect(url_for('admin_users'))
    
    # Delete user and associated races (cascade handles this)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.email} deleted successfully')
    return redirect(url_for('admin_users'))

# --- Password Reset Routes ---
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            
            # In a real app, you'd send an email here
            # For now, we'll just show the reset link
            reset_url = url_for('reset_password', token=token, _external=True)
            flash(f'Password reset link: {reset_url}')
        else:
            flash('If that email is registered, you will receive a reset link.')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset token')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('reset_password.html', token=token)
        
        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()
        flash('Password reset successfully')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

# --- Routes ---
@app.route('/')
def index():
    """Landing page - redirect to dashboard if logged in, otherwise to login"""
    import sys
    print('SCRIPT_NAME:', request.environ.get('SCRIPT_NAME'), file=sys.stderr)
    print('HTTP_X_SCRIPT_NAME:', request.environ.get('HTTP_X_SCRIPT_NAME'), file=sys.stderr)
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        if User.query.filter_by(username=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        # Create new user (username = email)
        user = User(
            username=email,  # Use email as username
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = bool(request.form.get('remember'))
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/settings')
@login_required
def settings():
    """Settings page with app configuration options"""
    return render_template('settings.html')

@app.route('/photos')
@login_required
def photos():
    """Photo gallery page showing all user's race photos"""
    try:
        # Get all photos for the current user through their races
        race_id_col = getattr(Race, 'id')
        race_user_id_col = getattr(Race, 'user_id')
        race_date_col = getattr(Race, 'race_date')
        photo_race_id_col = getattr(RacePhoto, 'race_id')
        photo_uploaded_col = getattr(RacePhoto, 'uploaded_at')
        
        photos_query = (db.session.query(RacePhoto, Race)
                       .join(Race, photo_race_id_col == race_id_col)
                       .filter(race_user_id_col == current_user.id)
                       .order_by(desc(race_date_col), desc(photo_uploaded_col))
                       .all())
        
        # Format photos with race information
        photos_data = []
        for photo, race in photos_query:
            photos_data.append({
                'photo': photo,
                'race': race,
                'race_date_formatted': race.race_date.strftime('%B %d, %Y') if race.race_date else 'Unknown Date'
            })
        
        return render_template('photos.html', photos_data=photos_data, total_photos=len(photos_data))
        
    except Exception as e:
        print(f'[PHOTOS_ERROR] user_id={getattr(current_user, "id", None)} error={e}', file=sys.stderr)
        flash('Error loading photos. Please try again.', 'warning')
        return redirect(url_for('dashboard'))

@app.route('/export_races')
@login_required
def export_races():
    """Export user's race data as CSV"""
    try:
        import csv
        import io
        from flask import make_response
        
        # Get user's races
        race_date_col = getattr(Race, 'race_date')
        races = Race.query.filter_by(user_id=current_user.id).order_by(desc(race_date_col)).all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Date', 'Race Name', 'Type', 'Start Time', 'Finish Time', 'Location', 'Weather', 'Notes'])
        
        # Write race data
        for race in races:
            writer.writerow([
                race.race_date.strftime('%Y-%m-%d') if race.race_date else '',
                race.race_name or '',
                race.race_type or '',
                race.race_time or '',
                race.finish_time or '',
                race.location or '',
                race.weather or '',
                race.notes or ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=race_data_{current_user.email}_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        print(f'[EXPORT_ERROR] user_id={current_user.id} error={e}', file=sys.stderr)
        flash('Error exporting race data. Please try again.', 'error')
        return redirect(url_for('settings'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/test-dashboard')
def test_dashboard():
    """Test endpoint to verify dashboard functionality without authentication"""
    try:
        # Get admin user for testing
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            return "Admin user not found", 404
            
        # Test the dashboard query
        race_date_col = getattr(Race, 'race_date')
        recent_races = (db.session.query(Race)
                        .filter_by(user_id=admin_user.id)
                        .order_by(desc(race_date_col))
                        .limit(5)
                        .all())
        
        return f"""
        <h1>Dashboard Test - SUCCESS!</h1>
        <p>✅ Database connection: Working</p>
        <p>✅ Race table access: Working</p>
        <p>✅ Weather columns: Available</p>
        <p>📊 Found {len(recent_races)} races for admin user</p>
        <p>🔗 <a href="/tracker/">Back to main page</a></p>
        """
    except Exception as e:
        return f"""
        <h1>Dashboard Test - FAILED</h1>
        <p>❌ Error: {str(e)}</p>
        <p>🔗 <a href="/tracker/">Back to main page</a></p>
        """, 500

@app.route('/add_race', methods=['GET', 'POST'])
@login_required
def add_race():
    if request.method != 'POST':
        return render_template('add_race.html')
    race = Race(
        user_id=current_user.id,
        race_name=request.form['race_name'],
        race_type=request.form['race_type'],
        race_date=datetime.strptime(request.form['race_date'], '%Y-%m-%d').date(),
        race_time=request.form.get('race_time', ''),
        finish_time=request.form['finish_time'],
        location=request.form.get('location', ''),
        weather=request.form.get('weather', ''),
        notes=request.form.get('notes', ''),
        race_page_url=request.form.get('race_page_url', '')
    )
    db.session.add(race)
    db.session.commit()
    # Handle up to 10 photo uploads, each with its own type and caption
    for i in range(1, 11):
        file = request.files.get(f'photo{i}')
        if file and file.filename != '' and allowed_file(file.filename):
            if file.filename and '.' in file.filename:
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'photos', filename))
                photo = RacePhoto(
                    race_id=race.id,
                    filename=filename,
                    original_filename=file.filename,
                    photo_type=request.form.get(f'photo_type{i}', 'other'),
                    caption=request.form.get(f'photo_caption{i}', '')
                )
                db.session.add(photo)
    pasted_saved = _save_pasted_images_from_form(race.id, request.form)
    db.session.commit()
    flash(f'Race added successfully! {pasted_saved} pasted image(s) saved.' if pasted_saved else 'Race added successfully!')
    return redirect(url_for('races'))

@app.route('/edit_race/<int:race_id>', methods=['GET', 'POST'])
@login_required
def edit_race(race_id):
    race = Race.query.filter_by(id=race_id, user_id=current_user.id).first_or_404()
    if request.method != 'POST':
        return render_template('edit_race.html', race=race)
    race.race_name = request.form['race_name']
    race.race_type = request.form['race_type']
    race.race_date = datetime.strptime(request.form['race_date'], '%Y-%m-%d').date()
    race.race_time = request.form.get('race_time', '')
    race.finish_time = request.form['finish_time']
    race.location = request.form.get('location', '')
    race.weather = request.form.get('weather', '')
    race.notes = request.form.get('notes', '')
    race.race_page_url = request.form.get('race_page_url', '')

    for i in range(1, 11):
        file = request.files.get(f'photo{i}')
        if file and file.filename != '' and allowed_file(file.filename):
            if file.filename and '.' in file.filename:
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'photos', filename))
                photo = RacePhoto(
                    race_id=race.id,
                    filename=filename,
                    original_filename=file.filename,
                    photo_type=request.form.get(f'photo_type{i}', 'other'),
                    caption=request.form.get(f'photo_caption{i}', '')
                )
                db.session.add(photo)
    pasted_saved = _save_pasted_images_from_form(race.id, request.form)
    db.session.commit()
    flash(f'Race updated successfully! {pasted_saved} pasted image(s) saved.' if pasted_saved else 'Race updated successfully!')
    return redirect(url_for('races'))

@app.route('/delete_race/<int:race_id>', methods=['POST'])
@login_required
def delete_race(race_id):
    race = Race.query.filter_by(id=race_id, user_id=current_user.id).first_or_404()
    # Delete associated photos from filesystem
    for photo in race.photos:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo.filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    db.session.delete(race)
    db.session.commit()
    flash('Race deleted successfully!')
    return redirect(url_for('races'))

@app.route('/uploads/photos/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), filename)

# --- PWA assets: manifest and service worker ---
@app.route('/manifest.json')
def serve_manifest():
    # Serve the web app manifest used in base.html
    root_dir = os.path.dirname(__file__)
    resp = send_from_directory(root_dir, 'manifest.json', mimetype='application/manifest+json')
    # Avoid stale manifests during active development
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

@app.route('/sw.js')
def serve_sw():
    # Service worker for PWA
    root_dir = os.path.dirname(__file__)
    resp = send_from_directory(root_dir, 'sw.js', mimetype='application/javascript')
    resp.headers['Cache-Control'] = 'no-cache'
    # Ensure the SW can control the subpath
    resp.headers['Service-Worker-Allowed'] = app.config.get('APPLICATION_ROOT', '/') or '/'
    return resp

@app.route('/statistics')
@login_required
def statistics():
    # Only show stats for the logged-in user
    races = Race.query.filter_by(user_id=current_user.id).all()
    # Group by race type
    race_types = {}
    for race in races:
        if race.race_type not in race_types:
            race_types[race.race_type] = []
        race_types[race.race_type].append(race)
    # Calculate statistics
    stats = {}
    for race_type, type_races in race_types.items():
        times = [r.time_to_seconds() for r in type_races]
        sorted_races = sorted(type_races, key=lambda x: x.race_date)
        first_race = sorted_races[0] if sorted_races else None
        last_race = sorted_races[-1] if sorted_races else None
        overall_trend = None
        if first_race and last_race and first_race != last_race:
            first_time = first_race.time_to_seconds()
            last_time = last_race.time_to_seconds()
            if first_time > 0:
                overall_trend = ((first_time - last_time) / first_time) * 100
        stats[race_type] = {
            'count': len(type_races),
            'best_time': min(times) if times else 0,
            'average_time': sum(times) / len(times) if times else 0,
            'recent_races': sorted(type_races, key=lambda x: x.race_date, reverse=True)[:5],
            'overall_trend': overall_trend
        }
    return render_template('statistics.html', stats=stats)

@app.route('/health')
def health_check():
    """Health check endpoint for Docker health monitoring"""
    return jsonify({'status': 'healthy', 'service': '5k-tracker'}), 200

@app.route('/tracker/health')
def tracker_health():
    return jsonify({"service": "tracker", "status": "healthy", "timestamp": datetime.now().isoformat()})

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _save_pasted_images_from_form(race_id: int, form_data) -> int:
    """Persist any pasted images included as data URLs in hidden inputs.

    Expected field patterns:
      pasted_image_<n> (value = data URL)
      pasted_type_<n>
      pasted_caption_<n>
    Returns number of images saved.
    """
    import base64, re
    saved = 0
    data_url_re = re.compile(r'^data:image/(png|jpe?g|gif|webp|bmp);base64,(.+)$', re.IGNORECASE)
    for key, value in form_data.items():
        if not key.startswith('pasted_image_'):
            continue
        m = data_url_re.match(value.strip())
        if not m:
            continue
        ext = m.group(1).lower()
        b64data = m.group(2)
        try:
            binary = base64.b64decode(b64data)
        except Exception:
            continue
        index = key.split('_')[-1]
        photo_type = form_data.get(f'pasted_type_{index}', 'other') or 'other'
        caption = form_data.get(f'pasted_caption_{index}', '') or ''
        # Normalize extension
        if ext == 'jpeg':
            ext = 'jpg'
        filename = f"{uuid.uuid4()}.{ext}"
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', filename)
        try:
            with open(photo_path, 'wb') as f:
                f.write(binary)
            photo = RacePhoto(
                race_id=race_id,
                filename=filename,
                original_filename=f"pasted.{ext}",
                photo_type=photo_type if photo_type in ['finish','medal','bib','other'] else 'other',
                caption=caption[:500]
            )
            db.session.add(photo)
            saved += 1
        except Exception:
            db.session.rollback()
            continue
    if saved:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return max(saved-1, 0)
    return saved

@app.route('/api/weather')
def api_weather():
    """Weather API endpoint for getting weather data"""
    place = request.args.get('place', '')
    datetime_str = request.args.get('datetime', '')
    
    if not place or not datetime_str:
        return jsonify({'error': 'Missing place or datetime parameter'}), 400
    
    try:
        # Parse the datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Use centralized mock for consistency
        weather = _mock_weather_for(place, dt)
        return jsonify({'weather': weather, 'location': {'name': place}})
         
    except ValueError as e:
        return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Weather service error: {str(e)}'}), 500

def _mock_weather_for(place: str, dt: datetime) -> dict:
    """Centralized mock weather generator (replace with real API later)."""
    # Optionally vary slightly by hour to feel dynamic
    hour = getattr(dt, 'hour', 7) or 7
    base_temp = 68 + ((hour - 7) % 6) * 2
    return {
        'temperature': base_temp,
        'wind_speed': 5,
        'humidity': 60,
        'weather_code': 0,
        'description': 'Clear sky'
    }

def get_weather_for_datetime(place, dt):
    """Fetch weather for a location and datetime string."""
    # Avoid HTTP self-calls; use internal helper for reliability and speed
    try:
        data = _mock_weather_for(place, dt)
        if data and 'temperature' in data:
            desc = data.get('description') or ''
            return f"{desc or 'Weather'}: {data.get('temperature', '?')}°F, wind {data.get('wind_speed', '?')} mph, humidity {data.get('humidity', '?')}%"
    except Exception:
        pass
    return "Weather unavailable"

def _is_missing_weather(value: str | None) -> bool:
    if not value:
        return True
    v = value.strip().lower()
    return v == '' or v == 'n/a' or v.startswith('weather unavailable')

def cache_race_weather(race, force: bool = False):
    """Cache weather for start and finish times; overwrite if force=True or values are missing."""
    place = race.location or ''
    # Start time
    date = getattr(race, 'race_date', None)
    if date is None:
        date = datetime.utcnow().date()
    # Start time
    time_str = getattr(race, 'race_time', None) or "07:00"
    time_parts = [int(x) for x in time_str.split(':') if x.isdigit()]
    if len(time_parts) == 3:
        dt_start = datetime(date.year, date.month, date.day, time_parts[0], time_parts[1], time_parts[2])
    elif len(time_parts) == 2:
        dt_start = datetime(date.year, date.month, date.day, time_parts[0], time_parts[1])
    else:
        dt_start = datetime(date.year, date.month, date.day, 7, 0)
    # Finish time (duration added to start) with support for decimals and 5K-only mm:ss:cc
    finish_str = (getattr(race, 'finish_time', None) or "00:45:00").strip()  # default 45m
    dur = _parse_duration_timedelta(finish_str, (getattr(race, 'race_type', None) or '').strip())
    dt_finish = dt_start + dur
    # Cache start/finish weather if missing or placeholder
    changed = False
    if force or _is_missing_weather(getattr(race, 'start_weather', None)):
        race.start_weather = get_weather_for_datetime(place, dt_start)
        changed = True
    if force or _is_missing_weather(getattr(race, 'finish_weather', None)):
        race.finish_weather = get_weather_for_datetime(place, dt_finish)
        changed = True
    if changed:
        try:
            db.session.add(race)
            db.session.commit()
        except Exception:
            db.session.rollback()
    return race.start_weather, race.finish_weather

# --- Duration parsing helpers ---
def _parse_duration_seconds(value: str, race_type: str) -> float:
    """Parse a duration string into seconds (float).
    Supports:
      - mm:ss.cc (dot), mm:ss
      - hh:mm:ss(.cc)
      - 5K-only mm:ss:cc (colon centiseconds)
      - single number = minutes
    """
    s = (value or '').strip()
    if not s:
        return 45 * 60.0
    try:
        parts = s.split(':')
        # 3-part ambiguous: either hh:mm:ss(.cc) or (5K-only) mm:ss:cc
        if len(parts) == 3:
            a, b, c = parts[0].strip(), parts[1].strip(), parts[2].strip()
            # If 5K and third is integer <= 99 and no decimals, treat as mm:ss:cc
            if race_type == '5K' and ('.' not in b) and ('.' not in c) and b.isdigit() and c.isdigit() and int(c) <= 99:
                mm = int(a)
                ss = int(b)
                cs = int(c)
                return mm * 60.0 + ss + (cs / 100.0)
            # Otherwise parse as hh:mm:s(.fraction)
            hh = int(a) if a else 0
            mm = int(b) if b else 0
            sec = float(c) if c else 0.0
            return hh * 3600.0 + mm * 60.0 + sec
        # 2-part: mm:ss(.cc)
        if len(parts) == 2:
            mm = int(parts[0]) if parts[0] else 0
            sec = float(parts[1]) if parts[1] else 0.0
            return mm * 60.0 + sec
        # 4-part: hh:mm:ss:cc (rare); treat last as centiseconds
        if len(parts) == 4:
            hh = int(parts[0])
            mm = int(parts[1])
            ss = int(parts[2])
            cs = int(parts[3])
            return hh * 3600.0 + mm * 60.0 + ss + (cs / 100.0)
        # Single number = minutes
        if len(parts) == 1:
            return float(parts[0]) * 60.0
    except Exception:
        pass
    # Fallback 45 min
    return 45 * 60.0

def _parse_duration_timedelta(value: str, race_type: str) -> timedelta:
    secs = _parse_duration_seconds(value, race_type)
    # Build timedelta with microsecond precision from float seconds
    whole = int(secs)
    frac = secs - whole
    micros = int(round(frac * 1_000_000))
    # Normalize rounding overflow (e.g., 59.999999 -> +1s)
    if micros >= 1_000_000:
        whole += 1
        micros -= 1_000_000
    return timedelta(seconds=whole, microseconds=micros)

# --- Time formatting helper ---
def format_race_time(race_type: str | None, time_str: str | None) -> str:
    """
    Display finish time by rules:
    - 5K ONLY: MM:SS.cc (two-digit centiseconds). Always show .cc; use .00 if missing.
    - Others: show HH:MM:SS if >=1h; otherwise MM:SS. Include .cc only if provided in input.
    Accepts inputs: mm:ss(.cc), hh:mm:ss(.cc), and (5K-only) mm:ss:cc.
    """
    if not time_str:
        return '—'
    rt = (race_type or '').strip()
    s_raw = time_str.strip()
    had_dot = '.' in s_raw
    secs = _parse_duration_seconds(s_raw, rt)

    # Convert float seconds to h/m/s/centi
    h = int(secs // 3600)
    rem = secs - h * 3600
    m = int(rem // 60)
    s = int(rem - m * 60)
    cs = int(round((secs - int(secs)) * 100))
    if cs == 100:
        cs = 0
        s += 1
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        h += 1

    if rt == '5K':
        total_minutes = h * 60 + m
        return f"{total_minutes:02d}:{s:02d}.{cs:02d}"

    # Non-5K
    if h > 0:
        base = f"{h:d}:{m:02d}:{s:02d}"
        return base + (f".{cs:02d}" if (had_dot and cs) else '')
    # Under 1 hour
    base = f"{m:02d}:{s:02d}"
    return base + (f".{cs:02d}" if (had_dot and cs) else '')

# --- Time-of-day formatting for start times (12-hour clock) ---
def to_12hr_time(time_str: str | None) -> str:
    """Convert 'HH:MM' or 'HH:MM:SS' string to 'HH:MM AM/PM'. Returns 'N/A' if blank."""
    if not time_str:
        return 'N/A'
    try:
        s = time_str.strip()
        if not s:
            return 'N/A'
        parts = [p for p in s.split(':') if p != '']
        if len(parts) < 2:
            return 'N/A'
        h = int(parts[0])
        m = int(parts[1])
        mer = 'AM'
        if h == 0:
            hh = 12
            mer = 'AM'
        elif 1 <= h <= 11:
            hh = h
            mer = 'AM'
        elif h == 12:
            hh = 12
            mer = 'PM'
        else:
            hh = h - 12
            mer = 'PM'
        return f"{hh:02d}:{m:02d} {mer}"
    except Exception:
        return time_str or 'N/A'

def init_db():
    """Initialize the database with tables"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

def create_default_users():
    """Create default users for testing"""
    with app.app_context():
        # Check if users already exist
        if not User.query.first():
            # Create default admin user
            admin = User(
                username='admin@example.com',  # Use email as username
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                is_admin=True  # Make this user an admin
            )
            admin.set_password(os.environ.get('ADMIN_DEFAULT_PASSWORD', 'admin123'))
            db.session.add(admin)
            
            # Create sample user
            user = User(
                username='runner@example.com',  # Use email as username
                email='runner@example.com',
                first_name='Test',
                last_name='Runner'
            )
            user.set_password(os.environ.get('USER_DEFAULT_PASSWORD', 'runner123'))
            db.session.add(user)
            db.session.commit()
            print("Default users created successfully!")



@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recent races
    race_date_col = getattr(Race, 'race_date')
    recent_races = (db.session.query(Race)
                    .filter_by(user_id=current_user.id)
                    .order_by(desc(race_date_col))
                    .limit(5)
                    .all())
    
    # Get personal records
    race_types = ['5K', '10K', 'Half Marathon', 'Marathon']
    personal_records = {}
    
    for race_type in race_types:
        best_race = Race.query.filter_by(user_id=current_user.id, race_type=race_type).all()
        if best_race:
            best_race = min(best_race, key=lambda x: x.time_to_seconds())
            personal_records[race_type] = best_race
    
    # Get race statistics
    total_races = Race.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html', 
                         recent_races=recent_races,
                         personal_records=personal_records,
                         total_races=total_races,
                         format_time=format_race_time)

@app.route('/races')
@login_required
def races():
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
        race_type = request.args.get('type', '').strip()

        base_query = Race.query.filter_by(user_id=current_user.id)
        if race_type:
            base_query = base_query.filter_by(race_type=race_type)

        per_page = 10
        total = base_query.count()
        race_date_col = getattr(Race, 'race_date')
        items = (base_query
                 .order_by(desc(race_date_col))
                 .offset((page - 1) * per_page)
                 .limit(per_page)
                 .all())
        print(f'[RACES_DIAG] user_id={getattr(current_user, "id", None)} total={total} items={len(items)}', file=sys.stderr)

        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
            @property
            def pages(self):
                return math.ceil(self.total / self.per_page) if self.per_page else 0
            @property
            def has_prev(self):
                return self.page > 1
            @property
            def has_next(self):
                return self.page < self.pages
            @property
            def prev_num(self):
                return self.page - 1 if self.has_prev else None
            @property
            def next_num(self):
                return self.page + 1 if self.has_next else None
            def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
                last = 0
                for num in range(1, self.pages + 1):
                    if (num <= left_edge or
                        (num > self.page - left_current - 1 and num < self.page + right_current) or
                        num > self.pages - right_edge):
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num

        races_pagination = SimplePagination(items, page, per_page, total)

        # Fetch and cache weather for each race (robust: log errors, never break loop)
        race_weather = {}
        for race in items:
            try:
                start_weather, finish_weather = cache_race_weather(race)
                race_weather[race.id] = {
                    'start': start_weather,
                    'finish': finish_weather
                }
            except Exception as e:
                print(f'[RACE_WEATHER_ERROR] race_id={getattr(race, "id", None)} finish_time={getattr(race, "finish_time", None)} error={e}', file=sys.stderr)
                race_weather[race.id] = {'start': 'N/A', 'finish': 'N/A'}
        try:
            db.session.commit()
        except Exception as e:
            print(f'[DB_COMMIT_ERROR] {e}', file=sys.stderr)
            db.session.rollback()

        def _linkify_notes(notes):
            import re
            if not notes:
                return ''
            url_pattern = r'(https?://\S+)'
            return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', notes.replace('\n', '<br>'))

        return render_template(
            'races.html',
            races=races_pagination,
            selected_type=race_type,
            linkify_notes=_linkify_notes,
            race_weather=race_weather,
            weather_icon=weather_icon,
            format_time=format_race_time,
            to_12hr=to_12hr_time,
            total_count=total,
            user_email=getattr(current_user, 'email', '')
        )
    except Exception as e:
        # Log rich diagnostics to stderr for correlation
        try:
            print('[RACES_ERROR]',
                  'user_id=', getattr(current_user, 'id', None),
                  'email=', getattr(current_user, 'email', None),
                  'cf_ray=', request.headers.get('cf-ray') or request.headers.get('Cf-Ray'),
                  'ua=', request.headers.get('User-Agent'),
                  'err=', repr(e),
                  file=sys.stderr)
            traceback.print_exc()
        except Exception:
            pass

        # Fallback: render empty list to avoid 500 for user
        class EmptyPagination:
            def __init__(self):
                self.items = []
                self.page = 1
                self.per_page = 10
                self.total = 0
            @property
            def pages(self):
                return 0
            @property
            def has_prev(self):
                return False
            @property
            def has_next(self):
                return False
            @property
            def prev_num(self):
                return None
            @property
            def next_num(self):
                return None
            def iter_pages(self, *args, **kwargs):
                return iter([])

        def _linkify_notes_2(notes):
            return ''

        flash('There was an issue loading your races. Showing empty list while we investigate.', 'warning')
        return render_template(
            'races.html',
            races=EmptyPagination(),
            selected_type='',
            linkify_notes=_linkify_notes_2,
            race_weather={},
            weather_icon=weather_icon,
            format_time=format_race_time,
            to_12hr=to_12hr_time,
            total_count=0,
            user_email=getattr(current_user, 'email', '')
        ), 200

@app.route('/workouts')
@login_required
def workouts():
    """Display user's workouts with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
        workout_type = request.args.get('type', '').strip()

        base_query = Workout.query.filter_by(user_id=current_user.id)
        if workout_type:
            base_query = base_query.filter_by(workout_type=workout_type)

        per_page = 15
        total = base_query.count()
        workout_date_col = getattr(Workout, 'workout_date')
        items = (base_query
                 .order_by(desc(workout_date_col))
                 .offset((page - 1) * per_page)
                 .limit(per_page)
                 .all())

        # Simple pagination class (reusing from races)
        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
            @property
            def pages(self):
                return math.ceil(self.total / self.per_page) if self.per_page else 0
            @property
            def has_prev(self):
                return self.page > 1
            @property
            def has_next(self):
                return self.page < self.pages
            @property
            def prev_num(self):
                return self.page - 1 if self.has_prev else None
            @property
            def next_num(self):
                return self.page + 1 if self.has_next else None

        workouts_pagination = SimplePagination(items, page, per_page, total)

        return render_template(
            'workouts.html',
            workouts=workouts_pagination,
            selected_type=workout_type,
            total_count=total
        )
    except Exception as e:
        print(f'[WORKOUTS_ERROR] user_id={getattr(current_user, "id", None)} error={e}', file=sys.stderr)
        flash('There was an issue loading your workouts.', 'warning')
        return redirect(url_for('dashboard'))

@app.route('/add_workout', methods=['GET', 'POST'])
@login_required
def add_workout():
    """Add a new workout"""
    if request.method == 'POST':
        try:
            workout_type = request.form.get('workout_type', '').strip()
            duration = request.form.get('duration', '').strip()
            distance = request.form.get('distance', '').strip()
            calories = request.form.get('calories', '').strip()
            heart_rate_avg = request.form.get('heart_rate_avg', '').strip()
            heart_rate_max = request.form.get('heart_rate_max', '').strip()
            notes = request.form.get('notes', '').strip()
            location = request.form.get('location', '').strip()
            workout_date = request.form.get('workout_date', '').strip()

            # Validation
            if not workout_type or not duration:
                flash('Workout type and duration are required.', 'error')
                return render_template('add_workout.html')

            # Parse and validate duration (HH:MM:SS or MM:SS)
            try:
                if ':' not in duration:
                    flash('Duration must be in format MM:SS or HH:MM:SS', 'error')
                    return render_template('add_workout.html')
                
                parts = duration.split(':')
                if len(parts) == 2:  # MM:SS
                    duration = f"00:{duration}"
                elif len(parts) != 3:  # Must be HH:MM:SS
                    flash('Duration must be in format MM:SS or HH:MM:SS', 'error')
                    return render_template('add_workout.html')
            except:
                flash('Invalid duration format', 'error')
                return render_template('add_workout.html')

            # Parse date
            workout_date_obj = None
            if workout_date:
                try:
                    workout_date_obj = datetime.strptime(workout_date, '%Y-%m-%d').date()
                except:
                    flash('Invalid date format', 'error')
                    return render_template('add_workout.html')

            # Create workout
            workout = Workout(
                user_id=current_user.id,
                workout_type=workout_type,
                duration=duration,
                distance=float(distance) if distance else None,
                calories=int(calories) if calories else None,
                heart_rate_avg=int(heart_rate_avg) if heart_rate_avg else None,
                heart_rate_max=int(heart_rate_max) if heart_rate_max else None,
                notes=notes if notes else None,
                location=location if location else None,
                workout_date=workout_date_obj
            )

            # Calculate pace if distance is provided
            if workout.distance and workout.duration:
                workout.pace = workout.calculate_pace()

            db.session.add(workout)
            db.session.commit()

            flash('Workout added successfully!', 'success')
            return redirect(url_for('workouts'))

        except Exception as e:
            print(f'[ADD_WORKOUT_ERROR] user_id={current_user.id} error={e}', file=sys.stderr)
            db.session.rollback()
            flash('Error adding workout. Please try again.', 'error')

    return render_template('add_workout.html')

@app.route('/import_healthkit_workouts', methods=['POST'])
@login_required
def import_healthkit_workouts():
    """Import workouts from HealthKit (for iOS app)"""
    try:
        # This will be called by the iOS app via JavaScript
        workouts_data = request.get_json()
        
        if not workouts_data or 'workouts' not in workouts_data:
            return jsonify({'error': 'No workout data provided'}), 400

        imported_count = 0
        for workout_data in workouts_data['workouts']:
            try:
                # Create workout from HealthKit data
                workout = Workout(
                    user_id=current_user.id,
                    workout_type=workout_data.get('type', 'Running'),
                    duration=workout_data.get('duration', '00:00:00'),
                    distance=workout_data.get('distance'),
                    calories=workout_data.get('calories'),
                    heart_rate_avg=workout_data.get('heartRateAvg'),
                    heart_rate_max=workout_data.get('heartRateMax'),
                    notes=f"Imported from HealthKit - {workout_data.get('sourceApp', 'Unknown')}",
                    workout_date=datetime.strptime(workout_data.get('date', ''), '%Y-%m-%d').date() if workout_data.get('date') else None
                )

                # Calculate pace if possible
                if workout.distance and workout.duration:
                    workout.pace = workout.calculate_pace()

                db.session.add(workout)
                imported_count += 1

            except Exception as e:
                print(f'[IMPORT_WORKOUT_ERROR] workout_data={workout_data} error={e}', file=sys.stderr)
                continue

        db.session.commit()
        return jsonify({
            'success': True,
            'imported': imported_count,
            'message': f'Successfully imported {imported_count} workouts from HealthKit'
        })

    except Exception as e:
        print(f'[IMPORT_HEALTHKIT_ERROR] user_id={current_user.id} error={e}', file=sys.stderr)
        db.session.rollback()
        return jsonify({'error': 'Failed to import workouts'}), 500

@app.route('/backfill_weather', methods=['POST'])
@login_required
def backfill_weather():
    """Backfill weather for all of the current user's races."""
    races = Race.query.filter_by(user_id=current_user.id).all()
    # Support forcing via form or query param
    def _truthy(v: str | None) -> bool:
        if not v:
            return False
        return v.lower() in ('1', 'true', 'yes', 'on')
    force = _truthy(request.args.get('force')) or _truthy(request.form.get('force'))
    updated = 0
    for r in races:
        try:
            before_sw, before_fw = getattr(r, 'start_weather', None), getattr(r, 'finish_weather', None)
            if force:
                # Explicitly clear cached values to ensure reset semantics
                r.start_weather = None
                r.finish_weather = None
            sw, fw = cache_race_weather(r, force=force)
            if force:
                updated += 1  # Count all processed when forcing
            else:
                if sw != before_sw or fw != before_fw:
                    updated += 1
        except Exception:
            continue
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    if force:
        flash(f'Weather forced refresh for {len(races)} race(s).')
    else:
        flash(f'Weather backfilled for {updated} race(s).')
    return redirect(url_for('races'))
