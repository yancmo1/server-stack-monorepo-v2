# --- Imports ---
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

# --- Load environment variables ---
load_dotenv('/Users/yancyshepherd/MEGA/PythonProjects/YANCY/shared/config/.env')

# --- Flask app and login manager setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('TRACKER_SECRET_KEY', 'changeme-please-set-TRACKER_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TRACKER_DATABASE_URI', 'sqlite:///race_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


# --- Ensure upload directory exists ---
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)

# --- Database setup ---
db = SQLAlchemy(app)



# --- Models ---
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
    race_time = db.Column(db.String(8), nullable=True)  # Format: HH:MM or HH:MM:SS
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
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    photo_type = db.Column(db.String(50), nullable=False)  # 'finish', 'medal', 'bib', 'other'
    caption = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RacePhoto {self.filename}>'

# --- Flask-Login user loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
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




@app.route('/add_race', methods=['GET', 'POST'])
@login_required
def add_race():
    if request.method == 'POST':
        race = Race(
            user_id=current_user.id,
            race_name=request.form['race_name'],
            race_type=request.form['race_type'],
            race_date=datetime.strptime(request.form['race_date'], '%Y-%m-%d').date(),
            race_time=request.form.get('race_time', ''),
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
        race.race_time = request.form.get('race_time', '')
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

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/weather')
@login_required
def get_weather():
    """Get weather data for a location and datetime"""
    place = request.args.get('place')
    datetime_str = request.args.get('datetime')
    
    if not place or not datetime_str:
        return jsonify({'error': 'Missing place or datetime parameter'}), 400
    
    try:
        # Parse the datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Geocode the location first
        def geocode(query):
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1&language=en&format=json"
            resp = requests.get(url, timeout=10)
            if not resp.ok:
                return None
            data = resp.json()
            if not data.get('results'):
                return None
            return data['results'][0]

        location = geocode(place)
        # Fallback: if not found, try just the first word (city name)
        if not location and ',' in place:
            city = place.split(',')[0].strip()
            location = geocode(city)
        if not location and ' ' in place:
            city = place.split(' ')[0].strip()
            location = geocode(city)
        if not location:
            return jsonify({'error': 'Could not find location. Try just the city name, e.g. "McAlester".'}), 400
        lat, lon = location['latitude'], location['longitude']
        
        # Get weather data
        # Format date for API (YYYY-MM-DD)
        date_str = dt.strftime('%Y-%m-%d')
        
        weather_url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': date_str,
            'end_date': date_str,
            'hourly': 'temperature_2m,wind_speed_10m,weather_code',
            'timezone': 'auto'
        }
        
        weather_response = requests.get(weather_url, params=params, timeout=10)
        
        if not weather_response.ok:
            return jsonify({'error': 'Failed to fetch weather data'}), 400
            
        weather_data = weather_response.json()
        
        if not weather_data.get('hourly'):
            return jsonify({'error': 'No weather data available for this date'}), 400
        
        # Find the closest hour to the requested time
        hourly = weather_data['hourly']
        target_hour = dt.hour
        
        # Get the data for the closest hour
        if target_hour < len(hourly['temperature_2m']):
            temperature = hourly['temperature_2m'][target_hour]
            wind_speed = hourly['wind_speed_10m'][target_hour]
            weather_code = hourly['weather_code'][target_hour]
        else:
            # Use the last available hour if target hour is not available
            temperature = hourly['temperature_2m'][-1] if hourly['temperature_2m'] else None
            wind_speed = hourly['wind_speed_10m'][-1] if hourly['wind_speed_10m'] else None
            weather_code = hourly['weather_code'][-1] if hourly['weather_code'] else None
        
        if temperature is None:
            return jsonify({'error': 'No weather data available for this time'}), 400
        
        return jsonify({
            'weather': {
                'temperature': round(temperature, 1),
                'wind_speed': round(wind_speed, 1) if wind_speed else 0,
                'weather_code': weather_code
            },
            'location': {
                'name': location['name'],
                'country': location.get('country', ''),
                'latitude': lat,
                'longitude': lon
            }
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
    except requests.RequestException as e:
        return jsonify({'error': f'Weather service unavailable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

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
            admin.set_password(os.environ.get('ADMIN_DEFAULT_PASSWORD', 'admin123'))
            db.session.add(admin)
            # Create sample user
            user = User(
                username='runner',
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

        



if __name__ == '__main__':
    init_db()
    create_default_users()
    
    # Run on port 5011 to match Docker Compose
    app.run(host='0.0.0.0', port=5554, debug=True)
