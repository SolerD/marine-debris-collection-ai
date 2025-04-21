import os
import sqlite3
import requests
import time
import json
from dotenv import load_dotenv
from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

load_dotenv()

#Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'Uploads'  
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  #16MB limit
app.secret_key = os.urandom(24).hex()  

#Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#SQLite database setup
DATABASE = 'database.db'

def init_db():
    """Initialize SQLite database with debris table."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debris (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                categories TEXT,
                gps_lat REAL,
                gps_lon REAL,
                country TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

#Geocoding cache
geocode_cache = {}
CACHE_FILE = 'geocode_cache.json'

#Load cache if exists and valid
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r') as f:
            content = f.read().strip()
            if content:  #Check if file is non-empty
                geocode_cache.update({tuple(map(float, k.split(','))): v for k, v in json.load(f).items()})
            else:
                print(f"Warning: {CACHE_FILE} is empty, initializing empty cache")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading {CACHE_FILE}: {e}, initializing empty cache")

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def reverse_geocode(lat, lon):
    """Reverse geocode GPS coordinates to get country using Nominatim."""
    cache_key = (lat, lon)
    if cache_key in geocode_cache:
        return geocode_cache[cache_key]
    
    base_url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'MarineDebrisApp/1.0 (student@lab6)' 
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        print(f"Reverse geocode status for lat={lat}, lon={lon}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            country = data.get('address', {}).get('country', 'Unknown')
            geocode_cache[cache_key] = country
            with open(CACHE_FILE, 'w') as f:
                json.dump({f"{k[0]},{k[1]}": v for k, v in geocode_cache.items()}, f)
            return country
        else:
            print(f"Reverse geocode error: {response.status_code}, {response.text}")
            return 'Unknown'
    except requests.RequestException as e:
        print(f"Reverse geocode failed: {e}")
        return 'Unknown'
    
    time.sleep(1)  #Nominatim rate limit

def classify_debris(image_path, description):
    """
    Classify image using Google Gemini.
    Returns (is_debris, categories).
    *** MANUALLY ADD: Replace with Google Gemini API call ***
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key = os.getenv('GEMINI_API_KEY'))
        #genai.configure(api_key='Using dotenv')  
        model = genai.GenerativeModel('gemini-1.5-flash')
        with open(image_path, 'rb') as img:
            image_data = img.read()
        prompt = f"""
            Analyze this image and description: "{description}".
            Determine if it contains marine debris per NOAA categories: Plastic, Metal, Glass, Rubber, Processed Wood, Fabric, Other.
            Return JSON: {{"is_debris": true/false, "categories": [list of matching categories]}}.
            If no debris, return empty categories.
        """
        response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': image_data}])
        result = json.loads(response.text.strip('```json\n```'))
        return result['is_debris'], result['categories']
    except Exception as e:
        print(f"LLM error: {e}")
        #Fallback: Mock classification
        import random
        debris_categories = ['Plastic', 'Metal', 'Glass', 'Rubber', 'Processed Wood', 'Fabric', 'Other']
        is_debris = 'plastic' in description.lower() or 'bottle' in description.lower()
        categories = ['Plastic'] if is_debris else []
        return is_debris, categories

def translate_description(description):
    
    return description  

@app.route('/', methods=['GET'])
def index():
    """Root route: Display form and submitted data."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, file_path, categories, gps_lat, gps_lon, country, description FROM debris')
        debris_data = cursor.fetchall()
    
    return render_template('index.html', debris_data=debris_data)

@app.route('/submit', methods=['POST'])
def submit():
    """Submit route: Process photo, description, and GPS."""
    if 'photo' not in request.files:
        flash('No photo provided', 'error')
        return redirect(url_for('index'))
    
    photo = request.files['photo']
    description = request.form.get('description', '')
    try:
        lat = float(request.form.get('lat'))
        lon = float(request.form.get('lon'))
    except (TypeError, ValueError):
        flash('Invalid GPS coordinates', 'error')
        return redirect(url_for('index'))
    
    if not photo or not allowed_file(photo.filename):
        flash('Invalid or missing photo', 'error')
        return redirect(url_for('index'))
    
    #Save photo
    filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    photo.save(file_path)
    
    #Translate description
    translated_description = translate_description(description)
    
    #Classify debris
    is_debris, categories = classify_debris(file_path, translated_description)
    
    if not is_debris:
        flash('Image does not contain marine debris', 'error')
        os.remove(file_path)
        return redirect(url_for('index'))
    
    #Reverse geocode
    country = reverse_geocode(lat, lon)
    
    #Store in database
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO debris (file_path, categories, gps_lat, gps_lon, country, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_path, ','.join(categories), lat, lon, country, translated_description))
        conn.commit()
    
    flash('Submission successful', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)  # *** CHECK: Set debug=False for production ***