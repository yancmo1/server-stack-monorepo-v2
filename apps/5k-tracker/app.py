def add_test_races():
    """Add generic test races for the 'runner' user."""
    with app.app_context():
        runner = User.query.filter_by(username='runner').first()
        if not runner:
            print("Runner user not found. Run create_default_users() first.")
            return
        from random import randint, choice
        race_types = ['5K', '10K', 'Half Marathon', 'Marathon']
        locations = ['Tulsa, OK', 'Dallas, TX', 'Oklahoma City, OK', 'Austin, TX']
        for i in range(1, 6):
            race = Race(
                user_id=runner.id,
                race_name=f"Test Race {i}",
                race_type=choice(race_types),
                race_date=datetime(2024, randint(1,12), randint(1,28)).date(),
                race_time=f"0{randint(6,9)}:00",
                finish_time=f"{randint(20,59)}:{randint(10,59)}",
                location=choice(locations),
                weather="Sunny, 70°F, wind 5 mph",
                notes=f"This is a test race entry number {i}."
            )
            db.session.add(race)
        db.session.commit()
        print("Test races added for runner.")
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
import re
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['APPLICATION_ROOT'] = '/tracker'
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SECRET_KEY'] = os.environ.get('TRACKER_SECRET_KEY', 'changeme-please-set-TRACKER_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TRACKER_DATABASE_URI', 'sqlite:///race_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# --- PrefixMiddleware for subpath support ---
class PrefixMiddleware:
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        import sys
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        path_info = environ.get('PATH_INFO', '')
        # Always set SCRIPT_NAME if HTTP_X_SCRIPT_NAME is present
        if script_name:
            environ['SCRIPT_NAME'] = script_name
        print(f"[PrefixMiddleware] script_name: {script_name}, path_info: {path_info}", file=sys.stderr)
        if script_name and path_info.startswith(script_name):
            environ['PATH_INFO'] = path_info[len(script_name):]
            print(f"[PrefixMiddleware] PATH_INFO rewritten to: {environ['PATH_INFO']}", file=sys.stderr)
        else:
            print("[PrefixMiddleware] No rewrite performed.", file=sys.stderr)
        return self.app(environ, start_response)

# PrefixMiddleware must be the outermost wrapper
app.wsgi_app = PrefixMiddleware(ProxyFix(app.wsgi_app, x_proto=1, x_host=1))

# Now initialize extensions, blueprints, etc.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@app.route('/logout')
def logout():
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
    import sys
    print('SCRIPT_NAME:', request.environ.get('SCRIPT_NAME'), file=sys.stderr)
    print('HTTP_X_SCRIPT_NAME:', request.environ.get('HTTP_X_SCRIPT_NAME'), file=sys.stderr)
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
        # Handle up to 5 photo uploads, each with its own type and caption
        for i in range(1, 6):
            file = request.files.get(f'photo{i}')
            if file and file.filename != '' and allowed_file(file.filename):
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
        db.session.commit()
        flash('Race added successfully!')
        return redirect(url_for('races'))
    return render_template('add_race.html')

@app.route('/edit_race/<int:race_id>', methods=['GET', 'POST'])
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
def get_weather():
    """Get weather data for a location and datetime"""
    place = request.args.get('place')
    datetime_str = request.args.get('datetime')
    
    if not place or not datetime_str:
        return jsonify({'error': 'Missing place or datetime parameter'}), 400
    
    try:
        # Parse the datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        today = datetime.utcnow().date()
        days_ago = (today - dt.date()).days

        # Helper: get state from input (e.g., "McAlester, OK" -> "OK")
        def extract_state(place):
            if ',' in place:
                parts = place.split(',')
                if len(parts) > 1:
                    return parts[1].strip()
            return None

        # Geocode the location, US only, try city,state, then city
        def geocode(query, state=None):
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=10&language=en&country=US&format=json"
            resp = requests.get(url, timeout=10)
            if not resp.ok:
                return None
            data = resp.json()
            if not data.get('results'):
                return None
            # If state provided, filter for state match (admin1)
            if state:
                for loc in data['results']:
                    if 'admin1' in loc and (loc['admin1'].lower().startswith(state.lower()) or state.lower() in loc['admin1'].lower()):
                        return loc
            # Otherwise, return first result
            return data['results'][0]

        state = extract_state(place)
        location = geocode(place, state)
        # Fallback: try just city name if not found
        if not location and ',' in place:
            city = place.split(',')[0].strip()
            location = geocode(city, state)
        if not location and ' ' in place:
            city = place.split(' ')[0].strip()
            location = geocode(city, state)
        if not location:
            return jsonify({'error': 'Could not find location. Try just the city name, e.g. "McAlester".'}), 400
        lat, lon = location['latitude'], location['longitude']

        date_str = dt.strftime('%Y-%m-%d')
        target_hour = dt.hour

        # Use historical API for dates more than 5 days ago
        if days_ago > 5:
            weather_url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': date_str,
                'end_date': date_str,
                'hourly': 'temperature_2m,wind_speed_10m,weather_code,relative_humidity_2m',
                'timezone': 'auto',
                'temperature_unit': 'fahrenheit'
            }
        else:
            weather_url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': date_str,
                'end_date': date_str,
                'hourly': 'temperature_2m,wind_speed_10m,weather_code,relative_humidity_2m',
                'timezone': 'auto',
                'temperature_unit': 'fahrenheit'
            }

        weather_response = requests.get(weather_url, params=params, timeout=10)
        if not weather_response.ok:
            return jsonify({'error': 'Failed to fetch weather data'}), 400
        weather_data = weather_response.json()
        if not weather_data.get('hourly'):
            return jsonify({'error': 'No weather data available for this date'}), 400
        hourly = weather_data['hourly']
        # Find the closest hour to the requested time
        if target_hour < len(hourly['temperature_2m']):
            temperature = hourly['temperature_2m'][target_hour]
            wind_speed = hourly['wind_speed_10m'][target_hour]
            weather_code = hourly['weather_code'][target_hour]
            humidity = hourly['relative_humidity_2m'][target_hour] if 'relative_humidity_2m' in hourly else None
        else:
            temperature = hourly['temperature_2m'][-1] if hourly['temperature_2m'] else None
            wind_speed = hourly['wind_speed_10m'][-1] if hourly['wind_speed_10m'] else None
            weather_code = hourly['weather_code'][-1] if hourly['weather_code'] else None
            humidity = hourly['relative_humidity_2m'][-1] if 'relative_humidity_2m' in hourly and hourly['relative_humidity_2m'] else None
        if temperature is None:
            return jsonify({'error': 'No weather data available for this time'}), 400
        return jsonify({
            'weather': {
                'temperature': round(temperature, 1),
                'wind_speed': round(wind_speed, 1) if wind_speed else 0,
                'humidity': round(humidity, 1) if humidity is not None else None,
                'weather_code': weather_code,
                'unit': 'F'
            },
            'location': {
                'name': location['name'],
                'country': location.get('country', ''),
                'state': location.get('admin1', ''),
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
def races():
    page = request.args.get('page', 1, type=int)
    race_type = request.args.get('type', '')
    
    query = Race.query.filter_by(user_id=current_user.id)
    
    if race_type:
        query = query.filter_by(race_type=race_type)
    
    races = query.order_by(Race.race_date.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('races.html', races=races, selected_type=race_type)

def parse_race_row(row, columns):
    # Map columns to Race fields
    data = {k: v.strip() for k, v in zip(columns, row)}
    # Try to extract city/state
    city = data.get('City', '')
    state = ''
    if ' ' in city:
        parts = city.split()
        if len(parts) > 1:
            state = parts[-1]
            city = ' '.join(parts[:-1])
    # Parse finish time (or gun time)
    finish_time = data.get('Finish Time') or data.get('Gun Time')
    # Try to parse date if present (not in your sample, but future-proof)
    race_date = datetime.utcnow().date()
    # Build Race dict
    return {
        'race_name': 'Imported Race',
        'race_type': '5K',
        'race_date': race_date,
        'race_time': '',
        'finish_time': finish_time,
        'location': f"{city}, {state}".strip(', '),
        'weather': '',
        'notes': '',
        'bib': data.get('Bib Number', ''),
        'age': data.get('Age', ''),
        'gender_place': data.get('Gender Place', ''),
        'ag_place': data.get('AG Place', ''),
        'pace': data.get('Pace', ''),
        'place': data.get('Place', ''),
        'name': data.get('Name', ''),
    }

@app.route('/import_results', methods=['GET', 'POST'])
@login_required
def import_results():
    imported = 0
    errors = []
    if request.method == 'POST':
        text = request.form.get('results_text', '')
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines or len(lines) < 2:
            errors.append('No data found.')
        else:
            # Try to auto-detect delimiter and header
            header = re.split(r'\s{2,}|\t|,', lines[0].strip())
            for row in lines[1:]:
                fields = re.split(r'\s{2,}|\t|,', row.strip())
                if len(fields) < 4:
                    errors.append(f'Row skipped (too few columns): {row}')
                    continue
                try:
                    race_data = parse_race_row(fields, header)
                    race = Race(
                        user_id=current_user.id,
                        race_name=race_data['race_name'],
                        race_type=race_data['race_type'],
                        race_date=race_data['race_date'],
                        race_time=race_data['race_time'],
                        finish_time=race_data['finish_time'],
                        location=race_data['location'],
                        weather=race_data['weather'],
                        notes=race_data['notes']
                    )
                    db.session.add(race)
                    imported += 1
                except Exception as e:
                    errors.append(f'Row error: {row} ({e})')
            db.session.commit()
            if imported:
                flash(f"Imported {imported} races!", 'success')
    return render_template('import_results.html', imported=imported if imported else None, errors=errors)
