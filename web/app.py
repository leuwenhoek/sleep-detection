from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime, timedelta 
import random 

app = Flask(__name__)

# --- Configuration to link to sleep_detector.py output ---
JSON_DIR = "JSON"
JSON_FILE_PATH = os.path.join(JSON_DIR, "sleep_detection_data.json")
# ---------------------------------------------------------

def load_vehicle_data():
    """
    Loads the latest list of vehicles from the shared JSON file.
    Robustly handles file access errors and unexpected JSON structure.
    """
    if not os.path.exists(JSON_FILE_PATH):
        return []
    
    try:
        # Use a common pattern: reading with 'r' is atomic enough for most OSs
        # when the file writer (sleep_detector.py) uses 'w' (overwrite).
        with open(JSON_FILE_PATH, "r") as f:
            data = json.load(f)
        
        # Ensure the data loaded is actually a list, as expected by the dashboard
        return data if isinstance(data, list) else []
        
    except (json.JSONDecodeError, OSError) as e:
        # This catches errors if the file is incomplete (being written) or corrupted.
        print(f"Error reading JSON file at {JSON_FILE_PATH}: {e}")
        return []

def analyze_data(vehicles):
    """Convert raw JSON -> stats + cleaned list for Jinja."""
    stats = {
        "total_vehicles": 0,
        "active": 0,
        "sleeping": 0,
        "by_type": {"car": 0, "truck": 0, "other": 0},
        "vehicles": []
    }

    for v in vehicles:
        stats["total_vehicles"] += 1
        v_type = v.get("type", "other").lower()
        if v_type not in ("car", "truck"):
            v_type = "other"
        stats["by_type"][v_type] += 1

        status_raw = v.get("status", "").strip()
        # Ensure sleep detection logic is comprehensive
        is_sleeping = status_raw in {"SLEEPING !!!", "sleeping", "asleep", "inactive", "Drowsy !"}
        status = "sleeping" if is_sleeping else "active"

        if is_sleeping:
            stats["sleeping"] += 1
        else:
            stats["active"] += 1

        # Format timestamp for display
        raw_time = v.get("last_update", "")
        formatted_time = raw_time 
        try:
            formatted_time = datetime.fromisoformat(raw_time.replace("Z", "+00:00")).strftime("%H:%M:%S")
        except:
            pass 

        stats["vehicles"].append({
            "id": v.get("id", "N/A"),
            "name": v.get("name", f"{v_type.title()} {v.get('id','')[-4:]}"),
            "type": v_type,
            "status": status,
            "last_update": formatted_time
        })

    return stats

@app.route("/")
def dashboard():
    vehicles = load_vehicle_data()
    data = analyze_data(vehicles)
    
    return render_template('dashboard.html', 
                           stats=data, 
                           vehicles=data["vehicles"])

@app.route("/api/data")
def api_data():
    vehicles = load_vehicle_data() 
    data = analyze_data(vehicles)
    
    return jsonify({
        "stats": {
            "total_vehicles": data["total_vehicles"],
            "active": data["active"],
            "sleeping": data["sleeping"],
            "by_type": data["by_type"]
        },
        "vehicles": data["vehicles"]
    })

if __name__ == "__main__":
    app.run(debug=True)