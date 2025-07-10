from flask import Flask, jsonify, request, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__)

CAR_LOCATIONS_FILE = 'car_locations.json'
USERS_FILE = 'users.json' 

MAX_LOCATION_ENTRIES = 1000 

if not os.path.exists(CAR_LOCATIONS_FILE):
    with open(CAR_LOCATIONS_FILE, 'w') as f:
        json.dump([], f) 

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/styles.css')
def style():
    return send_from_directory('.', 'styles.css')


@app.route('/location', methods=['POST'])
def receive_location():
    """
    Receives location data from the car tracker.
    Expected JSON format: {"latitude": float, "longitude": float}
    Implements a FIFO (First-In, First-Out) retention policy.
    """
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is None or longitude is None:
            return jsonify({'error': 'Missing latitude or longitude'}), 400

        timestamp = datetime.now().isoformat() + 'Z' 

        new_location = {
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': timestamp
        }

        with open(CAR_LOCATIONS_FILE, 'r+') as f:
            locations = json.load(f)
            
            if len(locations) >= MAX_LOCATION_ENTRIES:
                locations.pop(0)
                print(f"Removed oldest location to maintain {MAX_LOCATION_ENTRIES} entries.")
            
            locations.append(new_location)
            f.seek(0)
            json.dump(locations, f, indent=2) #
            f.truncate()
        print(f"Received location: {new_location}. Total entries: {len(locations)}") 
        return jsonify({'message': 'Location received and saved successfully!'}), 201

    except Exception as e:
        print(f"Error receiving location: {e}") 
        return jsonify({'error': str(e)}), 500

@app.route('/locations', methods=['GET'])
def get_all_locations():
    """
    Returns all stored car locations.
    """
    try:
        with open(CAR_LOCATIONS_FILE, 'r') as f:
            locations = json.load(f)
        return jsonify(locations), 200
    except FileNotFoundError:
        return jsonify([]), 200 
    except Exception as e:
        print(f"Error reading locations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users', methods=['GET'])
def get_users():
    if not os.path.exists(USERS_FILE):
        return jsonify([]), 200
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    return jsonify(users)

@app.route('/users', methods=['POST'])
def add_user():
    new_user = request.get_json()
    if not os.path.exists(USERS_FILE):
        users = []
    else:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)

    if any(user['username'] == new_user['username'] for user in users):
        return jsonify({'error': 'Username already exists'}), 400

    users.append(new_user)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    return jsonify({'message': 'User added successfully!'}), 201

@app.route('/login', methods=['POST'])
def login():
    credentials = request.get_json()
    username = credentials.get('username')
    password = credentials.get('password')

    if not os.path.exists(USERS_FILE):
        return jsonify({'error': 'Invalid username or password'}), 401

    with open(USERS_FILE, 'r') as f:
        users = json.load(f)

    for user in users:
        if user['username'] == username and user['password'] == password:
            return jsonify({'message': 'Login successful!'}), 200

    return jsonify({'error': 'Invalid username or password'}), 401

if __name__ == '__main__':
    if not os.path.exists(CAR_LOCATIONS_FILE):
        with open(CAR_LOCATIONS_FILE, 'w') as f:
            json.dump([], f)
    app.run(port=8000, debug=True) 