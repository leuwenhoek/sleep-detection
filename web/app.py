from flask import Flask, jsonify, render_template
import json
from datetime import datetime
import os
app = Flask(__name__)
# Assuming your JSON file is in a folder named 'JSON'
PATH = os.path.join('JSON','sleep_detection_data.json')

# --- Helper Function to Process Data and Stats ---
# The function now takes an optional 'error_state' argument.
def calculate_stats(data_list, error_state=False):
    if error_state:
        # Return statistics representing an error state
        return {
            'total_vehicles': 'N/A',
            'active': 'N/A',
            'sleeping': 'N/A',
            'by_type': {'car': 'N/A', 'truck': 'N/A'},
            'system_status': 'Not available (JSON file not found)'
        }
        
    total_vehicles = len(data_list)
    active = 0
    sleeping = 0
    by_type = {'car': 0, 'truck': 0}

    for vehicle in data_list:
        # Normalize status for consistency: check for 'active' ignoring case
        status_lower = vehicle.get('status', '').lower()
        v_type_lower = vehicle.get('type', '').lower()

        # NEW LOGIC: Explicitly skip counting for non-monitoring states
        if 'not running' in status_lower or 'not available' in status_lower:
            # This vehicle is excluded from active/sleeping/by_type counts
            continue
        
        # Count Active
        if 'active' in status_lower:
            active += 1
            
            # Count ACTIVE vehicles for the 'by_type' breakdown
            if v_type_lower in by_type:
                by_type[v_type_lower] += 1
        # Count Sleeping (this now only captures monitored non-active states like Drowsy/Sleeping)
        else:
            sleeping += 1

    return {
        'total_vehicles': total_vehicles,
        'active': active,
        'sleeping': sleeping,
        'by_type': by_type,
        'system_status': 'Running' # Indicate success
    }

# --- Flask Routes ---

@app.route('/')
def index():
    try:
        with open(PATH) as f:
            data = json.load(f)
        stats = calculate_stats(data)
        # Pass both 'vehicles' (the list) and 'stats' (the object)
        return render_template('dashboard.html', vehicles=data, stats=stats)
    except FileNotFoundError:
        # If the JSON file is not found, send empty data and error stats
        print(f"ERROR: Data file not found at {PATH}. Displaying 'Not Available' status.")
        stats = calculate_stats([], error_state=True)
        # We need to pass a list to 'vehicles' to avoid Jinja loop errors
        return render_template('dashboard.html', vehicles=[], stats=stats)


# This route serves fresh data for the AJAX polling in the front-end
@app.route('/api/data')
def get_data():
    try:
        with open(PATH) as f:
            data = json.load(f)
        stats = calculate_stats(data)
        
        # Return the full payload expected by the JavaScript updateDashboard function
        return jsonify({
            "vehicles": data,
            "stats": stats
        })
    except FileNotFoundError:
        # If the JSON file is not found, return an error payload
        stats = calculate_stats([], error_state=True)
        return jsonify({
            "vehicles": [],
            "stats": stats
        })

if __name__ == '__main__':
    app.run(debug=True)