
import os
import uuid
from datetime import datetime, timedelta
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv('/Users/yancyshepherd/MEGA/PythonProjects/YANCY/shared/config/.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('TRACKER_SECRET_KEY', 'changeme-please-set-TRACKER_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TRACKER_DATABASE_URI', 'sqlite:///race_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Weather API endpoint
@app.route('/api/weather', methods=['GET'])
@login_required
def api_weather():
    """API endpoint: ?place=PLACE&datetime=YYYY-MM-DDTHH:MM (ISO8601)"""
    place = request.args.get('place')
    dt_str = request.args.get('datetime')
    if not place or not dt_str:
        return jsonify({'error': 'Missing place or datetime'}), 400
    try:
        dt = datetime.fromisoformat(dt_str)
    except Exception as e:
        return jsonify({'error': f'Invalid datetime: {e}'}), 400
    lat, lon = geocode_place(place)
    if lat is None or lon is None:
        return jsonify({'error': f'Could not geocode place: {place}'}), 404
    weather = fetch_weather_forecast(lat, lon, dt)
    if not weather:
        return jsonify({'error': 'No weather data found'}), 404
    return jsonify({'place': place, 'lat': lat, 'lon': lon, 'datetime': dt_str, 'weather': weather})

# Weather API endpoint (must be after app = Flask(__name__))

import requests

# --- Weather Utilities ---
def geocode_place(place_name):
    """Use Open-Meteo's free geocoding API to get lat/lon for a place name"""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={place_name}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('results'):
            result = data['results'][0]
            return result['latitude'], result['longitude']
    return None, None

def fetch_weather_forecast(lat, lon, dt):
    """Fetch weather forecast for given lat/lon and datetime (ISO8601) using Open-Meteo"""
    # dt: datetime object
    date_str = dt.strftime('%Y-%m-%d')
    hour_str = dt.strftime('%H:00')
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,weathercode,wind_speed_10m,wind_direction_10m"
        f"&start={date_str}T{hour_str}&end={date_str}T{hour_str}"
        f"&timezone=auto"
    )
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        # Return the first (and only) hour's data if available
        if 'hourly' in data and 'time' in data['hourly'] and data['hourly']['time']:
            idx = 0
            return {
                'time': data['hourly']['time'][idx],
                'temperature': data['hourly']['temperature_2m'][idx],
                'precipitation': data['hourly']['precipitation'][idx],
                'weathercode': data['hourly']['weathercode'][idx],
                'wind_speed': data['hourly']['wind_speed_10m'][idx],
                'wind_direction': data['hourly']['wind_direction_10m'][idx],
            }
    return None

# Weather API endpoint (must be after app = Flask(__name__))
from flask_login import login_required
@app.route('/api/weather', methods=['GET'])
@login_required
def api_weather():
    """API endpoint: ?place=PLACE&datetime=YYYY-MM-DDTHH:MM (ISO8601)"""
    place = request.args.get('place')
    dt_str = request.args.get('datetime')
    if not place or not dt_str:
        return jsonify({'error': 'Missing place or datetime'}), 400
    try:
        dt = datetime.fromisoformat(dt_str)
    except Exception as e:
        return jsonify({'error': f'Invalid datetime: {e}'}), 400
    lat, lon = geocode_place(place)
    if lat is None or lon is None:
        return jsonify({'error': f'Could not geocode place: {place}'}), 404
    weather = fetch_weather_forecast(lat, lon, dt)
    if not weather:
        return jsonify({'error': 'No weather data found'}), 404
    return jsonify({'place': place, 'lat': lat, 'lon': lon, 'datetime': dt_str, 'weather': weather})

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)

db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to races
    races = db.relationship('Race', backref='runner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    race_name = db.Column(db.String(200), nullable=False)
    race_type = db.Column(db.String(50), nullable=False)  # '5K', '10K', 'Half Marathon', 'Marathon', 'Other'
    race_date = db.Column(db.Date, nullable=False)
    finish_time = db.Column(db.String(20), nullable=False)  # Format: HH:MM:SS
    location = db.Column(db.String(200))
    weather = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Photo relationships
    photos = db.relationship('RacePhoto', backref='race', lazy=True, cascade='all, delete-orphan')
    
    def time_to_seconds(self):
        """Convert finish time to seconds for comparison"""
        try:
            time_parts = self.finish_time.split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(time_parts) == 2:
                minutes, seconds = map(int, time_parts)
                return minutes * 60 + seconds
            return 0
        except:
            return 0
    
    def __repr__(self):
        return f'<Race {self.race_name} - {self.finish_time}>'

class RacePhoto(db.Model):

# Weather API endpoint (must be after app = Flask(__name__))
@app.route('/api/weather', methods=['GET'])
@login_required
def api_weather():
    """API endpoint: ?place=PLACE&datetime=YYYY-MM-DDTHH:MM (ISO8601)"""
    place = request.args.get('place')
    dt_str = request.args.get('datetime')
    if not place or not dt_str:
        return jsonify({'error': 'Missing place or datetime'}), 400
    try:
        dt = datetime.fromisoformat(dt_str)
    except Exception as e:
        return jsonify({'error': f'Invalid datetime: {e}'}), 400
    lat, lon = geocode_place(place)
    if lat is None or lon is None:
        return jsonify({'error': f'Could not geocode place: {place}'}), 404
    weather = fetch_weather_forecast(lat, lon, dt)
    if not weather:
        return jsonify({'error': 'No weather data found'}), 404
    return jsonify({'place': place, 'lat': lat, 'lon': lon, 'datetime': dt_str, 'weather': weather})
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    photo_type = db.Column(db.String(50), nullable=False)  # 'finish', 'medal', 'bib', 'other'
    caption = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RacePhoto {self.filename}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
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
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recent races
    recent_races = Race.query.filter_by(user_id=current_user.id).order_by(Race.race_date.desc()).limit(5).all()
    
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
                         total_races=total_races)

@app.route('/races')
@login_required
def races():
    page = request.args.get('page', 1, type=int)
    race_type = request.args.get('type', '')
    
    query = Race.query.filter_by(user_id=current_user.id)
    
    if race_type:
        query = query.filter_by(race_type=race_type)
    
    races = query.order_by(Race.race_date.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('races.html', races=races, selected_type=race_type)

@app.route('/add_race', methods=['GET', 'POST'])
@login_required
def add_race():
    if request.method == 'POST':
        race = Race(
            user_id=current_user.id,
            race_name=request.form['race_name'],
            race_type=request.form['race_type'],
            race_date=datetime.strptime(request.form['race_date'], '%Y-%m-%d').date(),
            finish_time=request.form['finish_time'],
            location=request.form.get('location', ''),
            weather=request.form.get('weather', ''),
            notes=request.form.get('notes', '')
        )
        
        db.session.add(race)
        db.session.commit()
        
        # Handle photo uploads
        if 'photos' in request.files:
            files = request.files.getlist('photos')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'photos', filename))
                    
                    photo = RacePhoto(
                        race_id=race.id,
                        filename=filename,
                        original_filename=file.filename,
                        photo_type=request.form.get('photo_type', 'other'),
                        caption=request.form.get('photo_caption', '')
                    )
                    db.session.add(photo)
        
        db.session.commit()
        flash('Race added successfully!')
        return redirect(url_for('races'))
    
    return render_template('add_race.html')

@app.route('/edit_race/<int:race_id>', methods=['GET', 'POST'])
@login_required
def edit_race(race_id):
    race = Race.query.filter_by(id=race_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        race.race_name = request.form['race_name']
        race.race_type = request.form['race_type']
        race.race_date = datetime.strptime(request.form['race_date'], '%Y-%m-%d').date()
        race.finish_time = request.form['finish_time']
        race.location = request.form.get('location', '')
        race.weather = request.form.get('weather', '')
        race.notes = request.form.get('notes', '')
        
        db.session.commit()
        flash('Race updated successfully!')
        return redirect(url_for('races'))
    
    return render_template('edit_race.html', race=race)

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

@app.route('/statistics')
@login_required
def statistics():
    # Get all races for the user
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
        stats[race_type] = {
            'count': len(type_races),
            'best_time': min(times) if times else 0,
            'average_time': sum(times) / len(times) if times else 0,
            'recent_races': sorted(type_races, key=lambda x: x.race_date, reverse=True)[:5]
        }
    
    return render_template('statistics.html', stats=stats)

@app.route('/health')
def health_check():
    """Health check endpoint for Docker health monitoring"""
    return jsonify({'status': 'healthy', 'service': '5k-tracker'}), 200

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
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User'
            )
            admin.set_password(os.environ.get('ADMIN_DEFAULT_PASSWORD', 'changeme-admin'))
            db.session.add(admin)
            
            # Create sample user
            user = User(
                username='runner',
                email='runner@example.com',
                first_name='Test',
                last_name='Runner'
            )
            user.set_password(os.environ.get('USER_DEFAULT_PASSWORD', 'changeme-user'))
            db.session.add(user)
            
            db.session.commit()
            print("Default users created successfully!")

if __name__ == '__main__':
    init_db()
    create_default_users()
    
    # Run on port 5011 to match Docker Compose
    app.run(host='0.0.0.0', port=5554, debug=True)
