from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from map_generator import generate_map
import json
import os
from datetime import datetime
import requests
import subprocess
import tempfile
import googlemaps
import psycopg2
from psycopg2.extras import RealDictCursor

# Load .env from central config
from dotenv import load_dotenv
load_dotenv('/Users/yancyshepherd/MEGA/PythonProjects/YANCY/config/.env')

app = Flask(__name__)
app.secret_key = os.environ.get('CLANMAP_SECRET_KEY', 'changeme-please-set-CLANMAP_SECRET_KEY')

# Database configuration - Postgres connection using environment variables
POSTGRES_DB = os.getenv("POSTGRES_DB", "cocstack")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cocuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

def get_bot_db_connection():
    """Get connection to the bot's Postgres database"""
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Postgres database: {e}")
        return None

def load_clan_data():
    """Load clan data from bot database"""
    conn = get_bot_db_connection()
    if not conn:
        print("Failed to connect to database")
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, role, location, latitude, longitude, favorite_troop, location_updated
            FROM players 
            WHERE name IS NOT NULL AND name != ''
            ORDER BY name
        """)
        rows = cursor.fetchall()
        conn.close()
        
        clan_data = []
        for row in rows:
            name, role, location, latitude, longitude, favorite_troop, updated = row
            player = {
                'name': name,
                'role': role or 'Member',
                'location': location or 'Unknown'
            }
            if latitude is not None and longitude is not None:
                player['latitude'] = latitude
                player['longitude'] = longitude
            if favorite_troop:
                player['favorite_troop'] = favorite_troop
            if updated:
                player['updated_at'] = updated
            clan_data.append(player)
        
        return clan_data
    except Exception as e:
        print(f"Error loading clan data from database: {e}")
        conn.close()
        return []

def save_clan_data(data):
    """Save clan data to bot database"""
    conn = get_bot_db_connection()
    if not conn:
        print("Failed to connect to database for saving")
        return False
    
    try:
        cursor = conn.cursor()
        for player in data:
            name = player['name']
            role = player.get('role', 'Member')
            location = player.get('location', 'Unknown')
            latitude = player.get('latitude')
            longitude = player.get('longitude')
            favorite_troop = player.get('favorite_troop')
            updated_at = player.get('updated_at', datetime.now().isoformat())
            
            # Update existing player
            cursor.execute("""
                UPDATE players SET 
                    role = %s, location = %s, latitude = %s, longitude = %s, 
                    favorite_troop = %s, location_updated = %s
                WHERE name = %s
            """, (role, location, latitude, longitude, favorite_troop, updated_at, name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving clan data: {e}")
        conn.close()
        return False

def geocode_location(location):
    """Convert location string to coordinates using Google Maps or OpenStreetMap"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if api_key:
        try:
            gmaps = googlemaps.Client(key=api_key)
            geocode_result = gmaps.geocode(location)
            if geocode_result:
                lat = geocode_result[0]['geometry']['location']['lat']
                lon = geocode_result[0]['geometry']['location']['lng']
                return lat, lon
        except Exception as e:
            print(f"Google Maps geocoding error: {e}")
    # Fallback to OpenStreetMap
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}&limit=1"
        headers = {'User-Agent': 'clan-map-app'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"OpenStreetMap geocoding error: {e}")
    return None, None

@app.route("/")
def index():
    # Only generate the map if it doesn't exist
    map_path = "static/folium_map.html"
    if not os.path.exists(map_path):
        clan_data = load_clan_data()
        generate_map(clan_data, output_file=map_path)
    return render_template("map.html")

@app.route("/submit")
def submit_form():
    # Get members who haven't been pinned on the map yet
    clan_data = load_clan_data()
    available_members = [member for member in clan_data 
                        if member.get('latitude') is None or member.get('longitude') is None]
    
    # Sort members alphabetically by name
    available_members.sort(key=lambda x: x['name'].lower())
    
    # Check if map snapshot exists, if not try to generate it
    has_snapshot = os.path.exists('static/images/map_snapshot.png')
    if not has_snapshot:
        try:
            snapshot_generated = generate_simple_map_image()
            has_snapshot = snapshot_generated and os.path.exists('static/images/map_snapshot.png')
        except Exception as e:
            print(f"Error generating map image: {e}")
            has_snapshot = False
    
    # Get mini map data for the submit page
    mini_map_data = generate_mini_map_data()
    
    return render_template("submit.html", 
                         available_members=available_members,
                         mini_map_data=mini_map_data,
                         has_snapshot=has_snapshot)

@app.route("/submit", methods=['POST'])
def submit_location():
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    favorite_troop = request.form.get('favorite_troop', '').strip()
    
    if not name or not location:
        flash('Name and location are required!', 'error')
        return redirect(url_for('submit_form'))
    
    # Load current clan data
    clan_data = load_clan_data()
    
    # Check if player already exists in data
    existing_player = None
    for i, player in enumerate(clan_data):
        if player['name'].lower() == name.lower():
            existing_player = i
            break
    
    # Geocode the location
    lat, lon = geocode_location(location)
    
    # Get player info from bot database
    role = 'Member'  # default
    conn = get_bot_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM players WHERE name = %s', (name,))
        result = cursor.fetchone()
        if result and result[0]:
            role = result[0]
        conn.close()
    
    # Create player data
    player_data = {
        'name': name,
        'location': location,
        'latitude': lat,
        'longitude': lon,
        'role': role,
        'favorite_troop': favorite_troop,
        'updated_at': datetime.now().isoformat()
    }
    
    # Update or add player
    if existing_player is not None:
        clan_data[existing_player] = player_data
        flash(f'Location updated for {name}!', 'success')
    else:
        clan_data.append(player_data)
        flash(f'Location added for {name}!', 'success')
    
    # Save updated data
    save_clan_data(clan_data)
    
    # Generate updated map image
    try:
        generate_simple_map_image()
    except Exception as e:
        print(f"Error generating map image after submission: {e}")
    
    return redirect(url_for('submit_form'))

@app.route("/api/players")
def api_players():
    """API endpoint to get all players data"""
    clan_data = load_clan_data()
    return jsonify(clan_data)

@app.route("/members")
def members_list():
    """Show list of all members and their locations"""
    clan_data = load_clan_data()
    
    # Separate pinned and unpinned members
    pinned_members = [member for member in clan_data 
                     if member.get('latitude') is not None and member.get('longitude') is not None]
    unpinned_members = [member for member in clan_data 
                       if member.get('latitude') is None or member.get('longitude') is None]
    
    return render_template("members.html", 
                         pinned_members=pinned_members, 
                         unpinned_members=unpinned_members,
                         total_members=len(clan_data))

@app.route("/admin/reset/<name>")
def admin_reset_location(name):
    """Reset a player's location (admin function)"""
    # Update in database
    conn = get_bot_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE players SET 
                location = 'Unknown', latitude = NULL, longitude = NULL, 
                favorite_troop = NULL, location_updated = NULL
            WHERE name = %s
        """, (name,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            
            # Update clan_data.json as well
            clan_data = load_clan_data()
            for player in clan_data:
                if player['name'].lower() == name.lower():
                    player['location'] = 'Unknown'
                    if 'latitude' in player:
                        del player['latitude']
                    if 'longitude' in player:
                        del player['longitude']
                    if 'favorite_troop' in player:
                        del player['favorite_troop']
                    if 'updated_at' in player:
                        del player['updated_at']
                    break
            save_clan_data(clan_data)
            
            flash(f'Reset location for {name}', 'success')
        else:
            conn.close()
            flash(f'Player {name} not found', 'error')
    else:
        flash('Database connection failed', 'error')
    
    return redirect(url_for('members_list'))

@app.route("/admin/set_role/<name>/<role>")
def admin_set_role(name, role):
    """Set a player's role manually (admin function)"""
    valid_roles = ['Leader', 'Co-Leader', 'Elder', 'Member']
    if role not in valid_roles:
        flash(f'Invalid role. Must be one of: {", ".join(valid_roles)}', 'error')
        return redirect(url_for('members_list'))
    
    # Update in database
    conn = get_bot_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE players SET role = %s WHERE name = %s', (role, name))
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            
            # Update clan_data.json as well
            clan_data = load_clan_data()
            for player in clan_data:
                if player['name'].lower() == name.lower():
                    player['role'] = role
                    break
            save_clan_data(clan_data)
            
            flash(f'Set {name} role to {role}', 'success')
        else:
            conn.close()
            flash(f'Player {name} not found', 'error')
    else:
        flash('Database connection failed', 'error')
    
    return redirect(url_for('members_list'))

def get_role_emoji(role):
    """Return emoji for clan role (matching Discord bot)"""
    role_emojis = {
        'Leader': '👑',
        'Co-Leader': '🔥',
        'Elder': '⭐',
        'Member': '👤',
        '': '❓'
    }
    return role_emojis.get(role, '❓')

# Make the function available in templates
app.jinja_env.globals.update(get_role_emoji=get_role_emoji)

def generate_simple_map_image():
    """Generate a simple map preview image using Pillow"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Get pinned members from the database
        conn = get_bot_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, role, location, latitude, longitude 
            FROM players 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ''')
        
        pinned_members = []
        for row in cursor.fetchall():
            pinned_members.append({
                'name': row[0],
                'role': row[1],
                'location': row[2],
                'latitude': float(row[3]),
                'longitude': float(row[4])
            })
        
        conn.close()
        
        if not pinned_members:
            return False
        
        # Create image using world map base
        width, height = 800, 400
        
        # Try to load the base world map image
        try:
            base_map_path = 'static/images/world_map_base.png'
            if os.path.exists(base_map_path):
                base_img = Image.open(base_map_path)
                # Resize to our desired dimensions
                base_img = base_img.resize((width, height), Image.Resampling.LANCZOS)
                img = base_img.convert('RGB')
            else:
                # Fallback to simple background if base map not found
                img = Image.new('RGB', (width, height), color='#b3d9ff')
        except Exception as e:
            print(f"Could not load base map, using fallback: {e}")
            img = Image.new('RGB', (width, height), color='#b3d9ff')
        
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Plot member locations as colored dots
        role_colors = {
            'Leader': '#dc3545',
            'Co-Leader': '#fd7e14', 
            'Elder': '#6f42c1',
            'Member': '#0d6efd'
        }
        
        # Simple coordinate mapping (very basic)
        for member in pinned_members:
            lat = member.get('latitude', 0)
            lon = member.get('longitude', 0)
            
            # Convert lat/lon to image coordinates (very simplified)
            x = int((lon + 180) * width / 360)
            y = int((90 - lat) * height / 180)
            
            # Ensure coordinates are within bounds
            x = max(10, min(width - 10, x))
            y = max(10, min(height - 10, y))
            
            role = member.get('role', 'Member')
            color = role_colors.get(role, '#0d6efd')
            
            # Draw larger, more visible dot for member location with better contrast
            radius = 10
            # Draw white background circle for contrast
            draw.ellipse([x-radius-2, y-radius-2, x+radius+2, y+radius+2], fill='white', outline='black', width=2)
            # Draw colored dot
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline='white', width=2)
        
        # Add title with background for readability (fixed positioning)
        title_text = f"Clan Map - {len(pinned_members)} Members Located"  # Removed emoji
        # Get text dimensions
        title_bbox = draw.textbbox((0, 0), title_text, font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        
        # Draw title background with proper padding
        title_x = (width - title_width) // 2
        title_y = 15  # More space from top
        draw.rectangle([title_x - 15, title_y - 8, title_x + title_width + 15, title_y + title_height + 8], 
                      fill='white', outline='black', width=2)
        draw.text((width//2, title_y + 5), title_text, font=font_large, anchor="mt", fill='#333')
        
        # Add legend with background (improved spacing)
        legend_y = height - 45  # More space from bottom
        legend_x = 20
        
        # Calculate legend background size
        legend_items = [(role, color) for role, color in role_colors.items() 
                       if len([p for p in pinned_members if p.get('role') == role]) > 0]
        
        if legend_items:
            # Draw legend background with better padding
            legend_width = len(legend_items) * 120
            draw.rectangle([10, legend_y - 15, legend_width + 10, legend_y + 25], 
                          fill='white', outline='black', width=2)
            
            # Draw legend items
            for role, color in legend_items:
                count = len([p for p in pinned_members if p.get('role') == role])
                if count > 0:
                    draw.ellipse([legend_x, legend_y, legend_x+10, legend_y+10], fill=color, outline='white', width=1)
                    draw.text((legend_x + 15, legend_y - 2), f"{role} ({count})", font=font_small, fill='#333')
                    legend_x += 120
        
        # Save the image
        os.makedirs('static/images', exist_ok=True)
        output_path = 'static/images/map_snapshot.png'
        img.save(output_path, 'PNG')
        print(f"Generated simple map image: {output_path}")
        return True
        
    except ImportError:
        print("PIL not available for map image generation")
        return False
    except Exception as e:
        print(f"Error generating simple map image: {e}")
        return False

def generate_mini_map_data():
    """Generate mini map data for the submit page"""
    try:
        clan_data = load_clan_data()
        pinned_members = [player for player in clan_data if player.get('latitude') and player.get('longitude')]
        
        return {
            'pinned_members': pinned_members,
            'total_located': len(pinned_members),
            'has_locations': len(pinned_members) > 0
        }
        
    except Exception as e:
        print(f"Error generating mini map data: {e}")
        return {'pinned_members': [], 'total_located': 0, 'has_locations': False}

def generate_map_snapshot():
    """Generate a PNG snapshot of the current map"""
    try:
        clan_data = load_clan_data()
        pinned_members = [player for player in clan_data if player.get('latitude') and player.get('longitude')]
        
        if not pinned_members:
            print("No pinned members found for snapshot")
            return False
        
        # Generate the map HTML
        map_obj = generate_map(pinned_members)
        
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_html:
            map_obj.save(temp_html.name)
            temp_html_path = temp_html.name
        
        try:
            # Output path for the PNG
            output_path = 'static/images/map_snapshot.png'
            os.makedirs('static/images', exist_ok=True)
            
            # Use wkhtmltoimage to convert HTML to PNG (if available)
            # Alternative: use headless Chrome/Chromium
            snapshot_cmd = None
            
            # Try different snapshot methods
            if os.path.exists('/usr/bin/wkhtmltoimage'):
                snapshot_cmd = [
                    'wkhtmltoimage',
                    '--width', '800',
                    '--height', '600',
                    '--crop-h', '600',
                    '--crop-w', '800',
                    '--quality', '90',
                    f'file://{temp_html_path}',
                    output_path
                ]
            elif os.path.exists('/usr/bin/chromium-browser') or os.path.exists('/usr/bin/google-chrome'):
                chrome_cmd = '/usr/bin/chromium-browser' if os.path.exists('/usr/bin/chromium-browser') else '/usr/bin/google-chrome'
                snapshot_cmd = [
                    chrome_cmd,
                    '--headless',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--window-size=800,600',
                    f'--screenshot={output_path}',
                    f'file://{temp_html_path}'
                ]
            
            if snapshot_cmd:
                result = subprocess.run(snapshot_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and os.path.exists(output_path):
                    print(f"Map snapshot generated successfully: {output_path}")
                    return True
                else:
                    print(f"Snapshot command failed: {result.stderr}")
            else:
                print("No snapshot tool available (tried wkhtmltoimage, chromium, chrome)")
            
            # Fallback: create a simple placeholder image with text
            create_placeholder_snapshot(output_path, pinned_members)
            return True
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
                
    except Exception as e:
        print(f"Error generating map snapshot: {e}")
        return False

def create_placeholder_snapshot(output_path, pinned_members):
    """Create a simple placeholder snapshot when proper snapshot tools aren't available"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple image with map info
        img = Image.new('RGB', (800, 600), color='#f0f8ff')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
            font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Draw title
        draw.text((400, 50), "🗺️ Clan Map Preview", font=font_large, anchor="mm", fill='#333')
        draw.text((400, 100), f"📍 {len(pinned_members)} Members Located", font=font_medium, anchor="mm", fill='#666')
        
        # Draw member locations
        y_pos = 150
        for i, member in enumerate(pinned_members[:15]):  # Show up to 15 members
            text = f"• {member['name']} - {member.get('location', 'Unknown')}"
            draw.text((50, y_pos), text, font=font_medium, fill='#444')
            y_pos += 25
        
        if len(pinned_members) > 15:
            draw.text((50, y_pos), f"... and {len(pinned_members) - 15} more!", font=font_medium, fill='#888')
        
        # Save the image
        img.save(output_path, 'PNG')
        print(f"Created placeholder snapshot: {output_path}")
        
    except ImportError:
        print("PIL not available, creating simple text file as placeholder")
        with open(output_path.replace('.png', '.txt'), 'w') as f:
            f.write(f"Clan Map Snapshot\n{len(pinned_members)} members located\n")
            for member in pinned_members:
                f.write(f"• {member['name']} - {member.get('location', 'Unknown')}\n")

if __name__ == "__main__":
    import os
    ssl_cert = '/app/ssl/dev.crt'
    ssl_key = '/app/ssl/dev.key'
    # Use shared SSL directory if available
    shared_ssl_cert = '/app/ssl/dev.crt'
    shared_ssl_key = '/app/ssl/dev.key'
    if os.path.exists('/app/ssl/fullchain.pem') and os.path.exists('/app/ssl/privkey.pem'):
        shared_ssl_cert = '/app/ssl/fullchain.pem'
        shared_ssl_key = '/app/ssl/privkey.pem'
        ssl_cert = shared_ssl_cert
        ssl_key = shared_ssl_key
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        print(f"[INFO] Starting Clan Map with SSL (HTTPS) on port 5552")
        app.run(debug=False, host="0.0.0.0", port=5552, ssl_context=(ssl_cert, ssl_key))
    else:
        print(f"[WARNING] SSL certificate or key not found. Starting in HTTP mode.")
        app.run(debug=False, host="0.0.0.0", port=5552)
