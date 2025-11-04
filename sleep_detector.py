import cv2
import mediapipe as mp
import numpy as np
import threading
import os
import platform
import json
import time
from datetime import datetime
from collections import deque

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

# Constants for detection
DEFAULT_EAR_THRESHOLD = 0.23  # Keep default threshold constant
CONSEC_FRAMES = 16
ALEART = True
MICROSLEEP_FRAMES = 30  # Frames indicating microsleep

# Variables for tracking state
sleep = drowsy = active = 0
status = ""
color = (0, 0, 0)
box_color = (0, 0, 0)

# Variable for adjustable threshold
current_threshold = DEFAULT_EAR_THRESHOLD

# Variables for custom threshold input
input_mode = False
input_text = ""
input_counter = 0  # For cursor blinking

# Variables for saving thresholds

if not os.path.exists(os.path.join("JSON","saved_thresholds.json")):
    os.mkdir("JSON")
save_thresholds_file = os.path.join("JSON","saved_thresholds.json")
saved_thresholds = []
recently_used = []  # List to track recently used thresholds
MAX_RECENT = 5  # Maximum number of recently used thresholds to track
naming_mode = False  # Whether we're in naming mode for a new threshold
name_input = ""
name_counter = 0  # For cursor blinking in name input
threshold_menu_open = False  # Whether threshold selection menu is open
current_threshold_name = "Default"  # Name of the currently selected threshold

# Variables for head pose
head_pose_angles = {'pitch': 0, 'yaw': 0, 'roll': 0}

# Variables for blink detection
blink_duration = 0
total_blinks = 0
last_blink_time = 0
blink_frequency = 0
microsleep_counter = 0
session_start_time = time.time()

# Variable for sleepiness percentage
sleep_percentage = 0
sleep_history = []  # To keep track of recent states for percentage calculation
MAX_HISTORY = 100  # Number of frames to consider for percentage

# Terminal message counter and limit
terminal_msg_count = 0
TERMINAL_MSG_LIMIT = 50  # Clear terminal after this many messages

# Add these near the other global variables (around line 30)
edit_counter = 0
input_counter = 0
name_counter = 0
edit_mode = False
edit_threshold_name = ""
edit_input = ""
consecutive_yawns = 0  # Add this for yawn detection

# ===== NEW: State tracking with timestamps =====
state_history = []
current_state = None
current_state_start = None
# ===============================================

def clear_terminal():
    """Clear terminal screen based on OS"""
    system_name = platform.system()
    if system_name == "Windows":
        os.system("cls")
    else:  # For Linux and MacOS
        os.system("clear")

def print_with_counter(message):
    """Print message and increment counter, clear terminal if needed"""
    global terminal_msg_count
    
    print(message)
    terminal_msg_count += 1
    
    if terminal_msg_count >= TERMINAL_MSG_LIMIT:
        clear_terminal()
        print("--- Terminal cleared after 50 messages ---")
        print(message)  # Reprint the current message after clearing
        terminal_msg_count = 1  # Reset counter (count the message we just printed)

def load_thresholds():
    global saved_thresholds
    try:
        if os.path.exists(save_thresholds_file):
            with open(save_thresholds_file, 'r') as f:
                data = json.load(f)
                saved_thresholds = data.get('thresholds', [])
                # Ensure values are floats
                for t in saved_thresholds:
                    t['value'] = float(t['value'])  # ADDED
                print_with_counter(f"Loaded {len(saved_thresholds)} saved thresholds")
        else:
            # Create default entry if file doesn't exist
            saved_thresholds = [{'name': 'Default', 'value': DEFAULT_EAR_THRESHOLD, 'last_used': datetime.now().isoformat()}]
            save_thresholds_to_file()
    except Exception as e:
        print_with_counter(f"Error loading thresholds: {e}")
        saved_thresholds = [{'name': 'Default', 'value': DEFAULT_EAR_THRESHOLD, 'last_used': datetime.now().isoformat()}]

def save_thresholds_to_file():
    """Save thresholds to file"""
    try:
        with open(save_thresholds_file, 'w') as f:
            json.dump({'thresholds': saved_thresholds}, f, indent=2)
        print_with_counter(f"Saved {len(saved_thresholds)} thresholds to file")
    except Exception as e:
        print_with_counter(f"Error saving thresholds: {e}")

# ===== NEW: Save state history =====
def save_state_history():
    """Save state history to JSON file"""
    try:
        with open(os.path.join("JSON","state_history.json"), "w") as f:
            json.dump(state_history, f, indent=2, default=str)
        print_with_counter("Saved state history to file")
    except Exception as e:
        print_with_counter(f"Error saving state history: {e}")
# ===================================

def add_to_recently_used(threshold_info):
    """Add a threshold to recently used list"""
    global recently_used
    
    # Update the "last_used" timestamp for the threshold
    for t in saved_thresholds:
        if t['name'] == threshold_info['name']:
            t['last_used'] = datetime.now().isoformat()
    
    # Add to recently used (avoiding duplicates)
    for i, item in enumerate(recently_used):
        if item['name'] == threshold_info['name']:
            recently_used.pop(i)
            break
    
    # Add to front of list
    recently_used.insert(0, threshold_info)
    
    # Limit the size
    if len(recently_used) > MAX_RECENT:
        recently_used.pop()
    
    # Save updated "last_used" capaces
    save_thresholds_to_file()

def save_current_threshold(name):
    """Save current threshold with given name"""
    global saved_thresholds, current_threshold, current_threshold_name
    
    # Check if name already exists
    for t in saved_thresholds:
        if t['name'].lower() == name.lower():
            # Update existing threshold
            t['value'] = current_threshold
            t['last_used'] = datetime.now().isoformat()
            print_with_counter(f"Updated threshold '{name}' with value {current_threshold}")
            current_threshold_name = name
            save_thresholds_to_file()
            return
    
    # Add new threshold
    new_threshold = {
        'name': name,
        'value': current_threshold,
        'last_used': datetime.now().isoformat()
    }
    
    saved_thresholds.append(new_threshold)
    current_threshold_name = name
    print_with_counter(f"Saved new threshold '{name}' with value {current_threshold}")
    
    # Add to recently used
    add_to_recently_used(new_threshold)
    
    # Save to file
    save_thresholds_to_file()

def delete_threshold(name):
    """Delete a threshold from saved thresholds"""
    global saved_thresholds, current_threshold_name, current_threshold
    
    for i, t in enumerate(saved_thresholds):
        if t['name'].lower() == name.lower():
            deleted_threshold = saved_thresholds.pop(i)
            print_with_counter(f"Deleted threshold '{name}' with value {deleted_threshold['value']}")
            
            # If deleted threshold was current, revert to default
            if current_threshold_name == name:
                current_threshold_name = "Default"
                current_threshold = DEFAULT_EAR_THRESHOLD
                print_with_counter(f"Reverted to Default threshold: {current_threshold}")
            
            # Remove from recently_used if present
            for i, item in enumerate(recently_used):
                if item['name'] == name:
                    recently_used.pop(i)
                    break
                    
            save_thresholds_to_file()
            return True
    print_with_counter(f"Threshold '{name}' not found")
    return False

def edit_threshold(name, new_value):
    try:
        new_value = float(new_value)
        if 0 < new_value < 1:
            for t in saved_thresholds:
                if t['name'].lower() == name.lower():
                    old_value = t['value']
                    t['value'] = round(float(new_value), 2)  # FIXED
                    t['last_used'] = datetime.now().isoformat()
                    print_with_counter(f"Edited threshold '{name}' from {old_value} to {new_value}")
                    
                    # Update current threshold if this was the active one
                    if current_threshold_name == name:
                        current_threshold = new_value
                    
                    save_thresholds_to_file()
                    return True
            print_with_counter(f"Threshold '{name}' not found")
            return False
        else:
            print_with_counter("Invalid threshold value. Must be between 0 and 1")
            return False
    except ValueError:
        print_with_counter("Invalid input. Please enter a numeric value")
        return False

def play_ALEART():
    """Function to display alert when sleeping is detected"""
    if ALEART:
        print_with_counter("ALERT: Wake up!")

def eye_aspect_ratio(eye):
    """Calculate Eye Aspect Ratio (EAR)"""
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def calculate_head_pose(face_landmarks, frame_width, frame_height):
    """Calculate head pose angles (pitch, yaw, roll)"""
    # 3D model points (generic face model)
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corner
        (-150.0, -150.0, -125.0),    # Left Mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ])
    
    # 2D image points from face landmarks
    image_points = np.array([
        (face_landmarks.landmark[1].x * frame_width, face_landmarks.landmark[1].y * frame_height),     # Nose tip
        (face_landmarks.landmark[175].x * frame_width, face_landmarks.landmark[175].y * frame_height),  # Chin
        (face_landmarks.landmark[33].x * frame_width, face_landmarks.landmark[33].y * frame_height),    # Left eye left corner
        (face_landmarks.landmark[263].x * frame_width, face_landmarks.landmark[263].y * frame_height),  # Right eye right corner
        (face_landmarks.landmark[61].x * frame_width, face_landmarks.landmark[61].y * frame_height),    # Left mouth corner
        (face_landmarks.landmark[291].x * frame_width, face_landmarks.landmark[291].y * frame_height)   # Right mouth corner
    ], dtype="double")
    
    # Camera internals
    focal_length = frame_width
    center = (frame_width/2, frame_height/2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]], dtype="double"
    )
    
    # Assuming no lens distortion
    dist_coeffs = np.zeros((4,1))
    
    # Solve PnP
    success, rotation_vector, translation_vector = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs)
    
    if success:
        # Convert rotation vector to rotation matrix
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        
        # Calculate Euler angles
        angles = cv2.RQDecomp3x3(rotation_matrix)[0]
        
        return {
            'pitch': angles[0],
            'yaw': angles[1], 
            'roll': angles[2]
        }
    
    return {'pitch': 0, 'yaw': 0, 'roll': 0}

def draw_button(frame, text, position, width, height, color=(200, 200, 200), text_color=(0, 0, 0)):
    """Draw a button on the frame"""
    x, y = position
    cv2.rectangle(frame, (x, y), (x + width, y + height), color, -1)
    cv2.rectangle(frame, (x, y), (x + width, y + height), (50, 50, 50), 2)
    
    # Calculate text position to center it in the button
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    text_x = x + (width - text_size[0]) // 2
    text_y = y + (height + text_size[1]) // 2
    
    cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
    
    return (x, y, x + width, y + height)  # Return button boundaries

def draw_threshold_menu(frame):
    """Draw the threshold selection menu with edit and delete options"""
    # Background for the menu
    menu_height = min(400, 50 + len(saved_thresholds) * 60 + 60)
    menu_width = 300
    menu_x = (frame.shape[1] - menu_width) // 2
    menu_y = (frame.shape[0] - menu_height) // 2
    
    # Semi-transparent overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
    
    # Menu background
    cv2.rectangle(frame, (menu_x, menu_y), (menu_x + menu_width, menu_y + menu_height), (240, 240, 240), -1)
    cv2.rectangle(frame, (menu_x, menu_y), (menu_x + menu_width, menu_y + menu_height), (0, 0, 0), 2)
    
    # Title
    cv2.putText(frame, "Saved Thresholds", (menu_x + 50, menu_y + 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # List of thresholds with buttons
    buttons = []
    y_offset = menu_y + 60
    
    # Sort thresholds by most recently used
    sorted_thresholds = sorted(saved_thresholds, 
                             key=lambda x: x.get('last_used', '1970-01-01'), 
                             reverse=True)
    
    for t in sorted_thresholds:
        # FIXED: Convert value to float before formatting
        btn = draw_button(frame, f"{t['name']}: {float(t['value']):.2f}", 
                         (menu_x + 10, y_offset), menu_width - 100, 30, 
                         color=(240, 240, 240))  # Define bg_color as a light gray color
        buttons.append(('threshold', t, btn))
        
        # Add Edit button
        edit_btn = draw_button(frame, "Edit", 
                             (menu_x + menu_width - 80, y_offset), 30, 30, 
                             color=(255, 200, 200))
        buttons.append(('edit', t, edit_btn))
        
        # Add Delete button
        del_btn = draw_button(frame, "Del", 
                            (menu_x + menu_width - 40, y_offset), 30, 30, 
                            color=(200, 200, 255))
        buttons.append(('delete', t, del_btn))
        
        y_offset += 50
    
    # Close button
    close_btn = draw_button(frame, "Close", 
                          (menu_x + menu_width//2 - 40, menu_y + menu_height - 40), 
                          80, 30, color=(200, 200, 200))
    buttons.append(('close', None, close_btn))
    
    return buttons

def truncate_text(text, max_length):
    """Truncate text to max_length and add ellipsis if needed"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def handle_mouse_click(event, x, y, flags, param):
    global current_threshold, input_mode, input_text, naming_mode, name_input
    global threshold_menu_open, edit_mode, edit_threshold_name, edit_input
    global current_threshold_name, recently_used  # ADDED
    
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    # If threshold menu is open, handle its buttons first
    if threshold_menu_open and 'menu_buttons' in param:
        for button_type, button_data, (x1, y1, x2, y2) in param['menu_buttons']:
            if x1 <= x <= x2 and y1 <= y <= y2:
                if button_type == 'close':
                    threshold_menu_open = False
                    return
                elif button_type == 'threshold':
                    # Apply selected threshold
                    current_threshold = float(button_data['value'])
                    current_threshold_name = button_data['name']
                    add_to_recently_used(button_data)
                    threshold_menu_open = False
                    print_with_counter(f"Applied threshold '{button_data['name']}' with value {button_data['value']}")
                    return
                elif button_type == 'delete':
                    delete_threshold(button_data['name'])
                    return
                elif button_type == 'edit':
                    edit_mode = True
                    edit_threshold_name = button_data['name']
                    edit_input = str(button_data['value'])
                    print_with_counter(f"Editing threshold '{button_data['name']}'")
                    return
        return
    
    # Handle edit mode input confirmation
    if edit_mode:
        return  # Handled in keyboard input
        
    # Check if any button was clicked when menus are not open
    if not input_mode and not naming_mode:
        # Check increase button
        inc_btn = param['inc_btn']
        if inc_btn[0] <= x <= inc_btn[2] and inc_btn[1] <= y <= inc_btn[3]:
            current_threshold += 0.01
            current_threshold = round(current_threshold, 2)
            print_with_counter(f"Threshold increased to: {current_threshold}")
            return
            
        # Check decrease button
        dec_btn = param['dec_btn']
        if dec_btn[0] <= x <= dec_btn[2] and dec_btn[1] <= y <= dec_btn[3]:
            current_threshold -= 0.01
            current_threshold = max(0.01, round(current_threshold, 2))  # Prevent negative threshold
            print_with_counter(f"Threshold decreased to: {current_threshold}")
            return
            
        # Check custom input button
        input_btn = param['input_btn']
        if input_btn[0] <= x <= input_btn[2] and input_btn[1] <= y <= input_btn[3]:  # Changed inc_btn to input_btn
            input_mode = True
            input_text = ""
            print_with_counter("Custom threshold input mode: active")
            return
            
        # Check save button
        save_btn = param['save_btn']
        if save_btn[0] <= x <= save_btn[2] and save_btn[1] <= y <= save_btn[3]:
            naming_mode = True
            name_input = ""
            print_with_counter("Enter a name for this threshold")
            return
            
        # Check load button
        load_btn = param['load_btn']
        if load_btn[0] <= x <= load_btn[2] and load_btn[1] <= y <= load_btn[3]:  # FIXED
            threshold_menu_open = True
            print_with_counter("Opening threshold selection menu")
            return

def handle_keyboard_input(key):
    """Handle keyboard input for custom threshold, naming, and editing"""
    global input_text, input_mode, current_threshold, naming_mode, name_input
    global threshold_menu_open, edit_mode, edit_input, edit_threshold_name
    
    # Close threshold menu with Escape
    if threshold_menu_open and key == 27:  # Escape key
        threshold_menu_open = False
        return
    
    # Process edit mode
    if edit_mode:
        # Confirm edit with Enter
        if key == 13:  # Enter key
            edit_threshold(edit_threshold_name, edit_input)
            edit_mode = False
            edit_input = ""
            edit_threshold_name = ""
            return
        
        # Backspace
        if key == 8:  # Backspace key
            edit_input = edit_input[:-1]
            return
            
        # Escape to cancel
        if key == 27:  # Escape key
            edit_mode = False
            edit_input = ""
            edit_threshold_name = ""
            print_with_counter("Edit cancelled")
            return
            
        # Add character if valid (numbers and decimal)
        if 48 <= key <= 57 or key == 46:  # Numbers or decimal point
            char = chr(key)
            if char == '.' and '.' in edit_input:
                return
            edit_input += char
            return
    
    # Process input mode
    if input_mode:
        # Confirm input with Enter
        if key == 13:  # Enter key
            try:
                value = float(input_text)
                if 0 < value < 1:  # Reasonable threshold range
                    current_threshold = round(value, 2)
                    print_with_counter(f"Threshold set to custom value: {current_threshold}")
                else:
                    print_with_counter("Invalid threshold value. Please enter a value between 0 and 1.")
            except ValueError:
                print_with_counter("Invalid input. Please enter a numeric value.")
            
            input_mode = False
            input_text = ""
            return
        
        # Backspace
        if key == 8:  # Backspace key
            input_text = input_text[:-1]
            return
            
        # Escape to cancel
        if key == 27:  # Escape key
            input_mode = False
            input_text = ""
            return
            
        # Add character if valid
        if 48 <= key <= 57 or key == 46:  # Numbers or decimal point
            char = chr(key)
            # Allow only one decimal point
            if char == '.' and '.' in input_text:
                return
            input_text += char
            return
    
    # Process naming mode
    if naming_mode:
        # Confirm name with Enter
        if key == 13:  # Enter key
            if name_input.strip():
                save_current_threshold(name_input.strip())
            else:
                print_with_counter("Name cannot be empty. Cancelled.")
            
            naming_mode = False
            name_input = ""
            return
        
        # Backspace
        if key == 8:  # Backspace key
            name_input = name_input[:-1]
            return
            
        # Escape to cancel
        if key == 27:  # Escape key
            naming_mode = False
            name_input = ""
            print_with_counter("Threshold naming cancelled")
            return
            
        # Add character if valid (allow letters, numbers, spaces, hyphens, underscores)
        if (32 <= key <= 126) and len(name_input) < 20:  # Printable ASCII with length limit
            name_input += chr(key)
            return

def update_sleep_percentage(state):
    """Update sleep percentage based on current state"""
    global sleep_percentage, sleep_history
    
    # Add current state to history
    if state == "SLEEPING !!!":
        sleep_history.append(2)
    elif state == "Drowsy !":
        sleep_history.append(1)
    else:
        sleep_history.append(0)
    
    # Limit history size
    if len(sleep_history) > MAX_HISTORY:
        sleep_history.pop(0)
    
    # Calculate weighted sleep percentage
    if sleep_history:
        total = sum(sleep_history)
        max_possible = 2 * len(sleep_history)
        sleep_percentage = (total / max_possible) * 100
    else:
        sleep_percentage = 0

# ===== NEW: State tracking with timestamps =====
def update_state_history(new_state):
    """Update state history when state changes"""
    global current_state, current_state_start, state_history
    
    current_time = datetime.now()
    
    if current_state is None:
        # First state
        current_state = new_state
        current_state_start = current_time
    elif current_state != new_state:
        # State changed, record previous state
        duration = (current_time - current_state_start).total_seconds()
        state_history.append({
            "state": current_state,
            "start": current_state_start,
            "end": current_time,
            "duration": duration
        })
        
        # Start new state
        current_state = new_state
        current_state_start = current_time
# ===============================================

def calculate_blink_rate():
    """Calculate blink rate in blinks per minute"""
    global blink_frequency, total_blinks, session_start_time
    
    current_time = time.time()
    session_duration = current_time - session_start_time
    
    if session_duration > 0:
        blink_frequency = total_blinks / (session_duration / 60)  # blinks per minute
    else:
        blink_frequency = 0
    return blink_frequency

def main():
    # Load saved thresholds
    load_thresholds()
    
    # Initialize webcam
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print_with_counter("Error: Could not open video capture device")
        return

    # Welcome message
    clear_terminal()
    print_with_counter("=== Drowsiness Detection System Started ===")
    print_with_counter("- Terminal will auto-clear after 50 messages")
    print_with_counter("- Press 'q' to quit the application")
    print_with_counter(f"- Loaded {len(saved_thresholds)} saved thresholds")

    # Create named window and set mouse callback
    cv2.namedWindow('Real-Time Eye State Detection')
    button_params = {'inc_btn': None, 'dec_btn': None, 'input_btn': None, 
                   'save_btn': None, 'load_btn': None, 'menu_buttons': []}
    cv2.setMouseCallback('Real-Time Eye State Detection', handle_mouse_click, button_params)

    # Add these globals if not already present
    global input_text, input_counter, input_mode, naming_mode, name_input, name_counter
    global edit_mode, edit_threshold_name, edit_input, edit_counter, threshold_menu_open
    global edit_mode, edit_threshold_name, edit_input, edit_counter
    global sleep, drowsy, active, status, color, box_color
    global blink_duration, total_blinks, last_blink_time, blink_frequency
    global microsleep_counter, session_start_time, head_pose_angles
    edit_mode = False
    edit_threshold_name = ""
    edit_input = ""
    edit_counter = 0

    # ===== NEW: Initialize state tracking =====
    global current_state, current_state_start
    current_state = None
    current_state_start = None
    # ==========================================

    try:
        while True:
            # Read frame from webcam
            ret, frame = video_capture.read()
            if not ret:
                raise RuntimeError("Failed to read frame from webcam")
            if not ret:
                print_with_counter("Error: Could not read frame")
                break
            
            # Process frame
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)

            # Draw threshold adjustment buttons
            btn_width, btn_height = 80, 40
            inc_btn = draw_button(frame, "Thresh+", (10, frame.shape[0] - 50), btn_width, btn_height)
            dec_btn = draw_button(frame, "Thresh-", (100, frame.shape[0] - 50), btn_width, btn_height)
            input_btn = draw_button(frame, "Custom", (190, frame.shape[0] - 50), btn_width, btn_height)
            save_btn = draw_button(frame, "Save", (280, frame.shape[0] - 50), btn_width, btn_height)
            load_btn = draw_button(frame, "Load", (370, frame.shape[0] - 50), btn_width, btn_height)

            button_params['inc_btn'] = inc_btn
            button_params['dec_btn'] = dec_btn
            button_params['input_btn'] = input_btn
            button_params['save_btn'] = save_btn
            button_params['load_btn'] = load_btn
            
            # Draw custom input field if active
            if input_mode:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                
                cv2.rectangle(frame, (frame.shape[1]//2 - 100, frame.shape[0]//2 - 30), 
                            (frame.shape[1]//2 + 100, frame.shape[0]//2 + 30), 
                            (255, 255, 255), -1)
                cv2.rectangle(frame, (frame.shape[1]//2 - 100, frame.shape[0]//2 - 30), 
                            (frame.shape[1]//2 + 100, frame.shape[0]//2 + 30), 
                            (0, 0, 0), 2)
                
                cv2.putText(frame, "Enter threshold value:", 
                          (frame.shape[1]//2 - 100, frame.shape[0]//2 - 40), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                display_text = input_text
                input_counter = (input_counter + 1) % 30
                if input_counter < 15:
                    display_text += "|"
                
                cv2.putText(frame, display_text, 
                          (frame.shape[1]//2 - 50, frame.shape[0]//2 + 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
                cv2.putText(frame, "Press Enter to confirm, Esc to cancel", 
                          (frame.shape[1]//2 - 140, frame.shape[0]//2 + 50), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw naming input field if active
            elif naming_mode:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                
                cv2.rectangle(frame, (frame.shape[1]//2 - 150, frame.shape[0]//2 - 30), 
                            (frame.shape[1]//2 + 150, frame.shape[0]//2 + 30), 
                            (255, 255, 255), -1)
                cv2.rectangle(frame, (frame.shape[1]//2 - 150, frame.shape[0]//2 - 30), 
                            (frame.shape[1]//2 + 150, frame.shape[0]//2 + 30), 
                            (0, 0, 0), 2)
                
                cv2.putText(frame, "Name this threshold:", 
                          (frame.shape[1]//2 - 100, frame.shape[0]//2 - 40), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                display_name = name_input
                name_counter = (name_counter + 1) % 30
                if name_counter < 15:
                    display_name += "|"
                
                cv2.putText(frame, display_name, 
                          (frame.shape[1]//2 - 140, frame.shape[0]//2 + 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
                cv2.putText(frame, "Press Enter to save, Esc to cancel", 
                          (frame.shape[1]//2 - 140, frame.shape[0]//2 + 50), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw edit input field if active
            elif edit_mode:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                
                cv2.rectangle(frame, (frame.shape[1]//2 - 100, frame.shape[0]//2 - 30), 
                            (frame.shape[1]//2 + 100, frame.shape[0]//2 + 30), 
                            (255, 255, 255), -1)
                cv2.rectangle(frame, (frame.shape[1]//2 - 100, frame.shape[0]//2 - 30), 
                            (frame.shape[1]//2 + 100, frame.shape[0]//2 + 30), 
                            (0, 0, 0), 2)
                
                cv2.putText(frame, f"Edit {edit_threshold_name}:", 
                          (frame.shape[1]//2 - 100, frame.shape[0]//2 - 40), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                display_edit = edit_input
                edit_counter = (edit_counter + 1) % 30
                if edit_counter < 15:
                    display_edit += "|"
                
                cv2.putText(frame, display_edit, 
                          (frame.shape[1]//2 - 50, frame.shape[0]//2 + 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
                cv2.putText(frame, "Press Enter to save, Esc to cancel", 
                          (frame.shape[1]//2 - 140, frame.shape[0]//2 + 50), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw threshold selection menu if open
            elif threshold_menu_open:
                menu_buttons = draw_threshold_menu(frame)
                button_params['menu_buttons'] = menu_buttons
            else:
                button_params['menu_buttons'] = []  # Clear menu buttons when menu is closed
            
            # Display current threshold info
            threshold_text = f"Threshold: {current_threshold} ({truncate_text(current_threshold_name, 15)})"
            cv2.putText(frame, threshold_text, 
                      (10, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 
                      0.6, (0, 0, 0), 2)
            
            # Display sleepiness percentage
            percentage_color = (0, 255, 0) if sleep_percentage < 30 else (0, 165, 255) if sleep_percentage < 60 else (0, 0, 255)
            cv2.putText(frame, f"Sleepiness: {sleep_percentage:.1f}%", 
                      (frame.shape[1] - 220, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                      0.6, percentage_color, 2)
            
            # Display head pose
            cv2.putText(frame, f"Head: P:{head_pose_angles['pitch']:.1f} Y:{head_pose_angles['yaw']:.1f} R:{head_pose_angles['roll']:.1f}", 
                      (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Display blink rate
            cv2.putText(frame, f"Blink Rate: {blink_frequency:.1f}/min", 
                      (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Get frame dimensions and face bounding box
                    h, w, _ = frame.shape
                    face_points = np.array([(landmark.x * w, landmark.y * h) for landmark in face_landmarks.landmark])
                    
                    # Calculate bounding box coordinates with padding
                    padding = 20
                    x_min = max(0, int(np.min(face_points[:, 0])) - padding)  # Add closing parenthesis
                    y_min = max(0, int(np.min(face_points[:, 1])) - padding)  # Add closing parenthesis
                    x_max = min(w, int(np.max(face_points[:, 0])) + padding)  # Add closing parenthesis
                    y_max = min(h, int(np.max(face_points[:, 1])) + padding)  # Add closing parenthesis
                    
                    # Extract eye coordinates
                    left_eye = np.array([(face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h) 
                                      for i in [33, 160, 158, 133, 153, 144]])
                    right_eye = np.array([(face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h) 
                                       for i in [362, 385, 387, 263, 373, 380]])
                    
                    # Calculate EAR
                    left_ear = eye_aspect_ratio(left_eye)
                    right_ear = eye_aspect_ratio(right_eye)
                    ear = (left_ear + right_ear) / 2.0
                    
                    # Calculate head pose
                    head_pose_angles = calculate_head_pose(face_landmarks, w, h)
                    
                    # Blink detection
                    current_time = time.time()
                    is_eye_closed = ear < current_threshold
                    if is_eye_closed:
                        blink_duration += 1
                        if blink_duration == 1:  # Start of blink
                            if current_time - last_blink_time > 0.5:  # Valid blink (not continuation)
                                total_blinks += 1
                                last_blink_time = current_time
                    else:
                        if blink_duration > 0:  # End of blink
                            if blink_duration > MICROSLEEP_FRAMES:
                                microsleep_counter += 1
                                print_with_counter(f"Microsleep detected! Duration: {blink_duration} frames")
                        blink_duration = 0
                    
                    # Update blink rate
                    calculate_blink_rate()
                    
                    # Display current EAR value
                    cv2.putText(frame, f"EAR: {ear:.2f}", 
                              (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                              0.6, (0, 0, 0), 2)
                    
                    # Use the adjustable threshold for detection
                    old_status = status
                    if ear < current_threshold:
                        sleep += 1
                        drowsy = active = 0
                        if sleep > CONSEC_FRAMES:
                            status = "SLEEPING !!!"
                            color = (0, 0, 255)  # Red text
                            box_color = (0, 0, 255)  # Red box
                            threading.Thread(target=play_ALEART).start()
                    elif current_threshold <= ear < current_threshold + 0.04:
                        drowsy += 1
                        sleep = active = 0
                        if drowsy > CONSEC_FRAMES:
                            status = "Drowsy !"
                            color = (255, 0, 255)  # Magenta text
                            box_color = (255, 0, 255)  # Magenta box
                    else:
                        active += 1
                        sleep = drowsy = 0
                        if active > CONSEC_FRAMES:
                            status = "Active :)"
                            color = (0, 255, 0)  # Green text
                            box_color = (0, 255, 0)  # Green box
                    
                    # ===== NEW: Update state history =====
                    if status and old_status != status:
                        print_with_counter(f"Status changed to: {status} (EAR: {ear:.2f})")
                        update_state_history(status)
                    # ====================================
                    
                    # Update sleep percentage
                    update_sleep_percentage(status)
                    
                    # Alert when sleepiness is high
                    if sleep_percentage > 50 and sleep_percentage % 10 < 0.1:
                        print_with_counter(f"WARNING: Sleepiness at {sleep_percentage:.1f}%!")
                    
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), box_color, 2)
                    
                    # Display status with background
                    text_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 1, 3)[0]
                    cv2.rectangle(frame, (10, 5), (text_size[0] + 20, 40), (255, 255, 255), -1)
                    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
            else:
                # Print message if no face is detected
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Reset counters =when no face
                sleep = drowsy = active = 0
                status = ""
                blink_duration = 0  # Reset blink duration

            # Display frame
            cv2.imshow('Real-Time Eye State Detection', frame)

            # Check for key presses
            key = cv2.waitKey(5) & 0xFF
            
            # Handle keyboard input
            handle_keyboard_input(key)
            
            # Quit on 'q'
            if key == ord('q'):
                print_with_counter("Quitting application...")
                break

    finally:
        # ===== NEW: Finalize state history =====
        if current_state is not None:
            current_time = datetime.now()
            duration = (current_time - current_state_start).total_seconds()
            state_history.append({
                "state": current_state,
                "start": current_state_start,
                "end": current_time,
                "duration": duration
            })
            save_state_history()
        # ======================================
        
        # Session summary
        session_duration = time.time() - session_start_time
        final_blink_rate = calculate_blink_rate()
        recommendation = "Take a break and rest if possible." if sleep_percentage > 50 or microsleep_counter >= 10 else "Continue monitoring if driving or performing critical tasks."
        
        print_with_counter("=== Session Summary ===")
        print_with_counter(f"Duration: {session_duration/60:.1f} minutes")
        print_with_counter(f"Total Blinks: {total_blinks}")
        print_with_counter(f"Average Blink Rate: {final_blink_rate:.1f} blinks/minute")
        print_with_counter(f"Microsleep Episodes: {microsleep_counter}")
        print_with_counter(f"Final Sleepiness: {sleep_percentage:.1f}%")
        print_with_counter(f"Final Recommendation: {recommendation}")
        print_with_counter("=== Application terminated ===")
        
        # Save session summary to HTML file
        if not os.path.exists('session'):
            os.mkdir('session')
        session_summary = os.path.join('session','session_summary.html')
        with open(session_summary, "w") as f:
            # Generate HTML table for state history
            state_table_html = ""
            if state_history:
                for entry in state_history:
                    start_time = entry['start'].strftime("%Y-%m-%d %H:%M:%S")
                    end_time = entry['end'].strftime("%Y-%m-%d %H:%M:%S")
                    duration_min = entry['duration'] / 60
                    state_color = {
                        "Active :)": "green",
                        "Drowsy !": "orange",
                        "SLEEPING !!!": "red"
                    }.get(entry['state'], "gray")
                    
                    state_table_html += f"""
                    <tr>
                        <td class="metric-name" style="color: {state_color}">{entry['state']}</td>
                        <td class="metric-value">{start_time}</td>
                        <td class="metric-value">{end_time}</td>
                        <td class="metric-value">{duration_min:.1f} min</td>
                    </tr>
                    """
            else:
                state_table_html = """
                    <tr>
                        <td colspan="4" class="metric-value">No state data recorded</td>
                    </tr>
                """
            
            # Generate timeline visualization
            timeline_html = ""
            if state_history:
                total_duration = session_duration
                for entry in state_history:
                    percentage = (entry['duration'] / total_duration) * 100
                    state_color = {
                        "Active :)": "#10B981",
                        "Drowsy !": "#F59E0B",
                        "SLEEPING !!!": "#EF4444"
                    }.get(entry['state'], "#94A3B8")
                    
                    timeline_html += f"""
                    <div class="timeline-segment" style="width: {percentage}%; background-color: {state_color};">
                        <span class="timeline-label">{entry['state']}</span>
                    </div>
                    """
            else:
                timeline_html = '<div class="timeline-segment" style="width: 100%; background-color: #94A3B8;"><span class="timeline-label">No Data</span></div>'
            
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drowsiness Detection Session Summary</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Anton:wght@400&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Poppins', sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            color: #e2e8f0;
            position: relative;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            position: relative;
            z-index: 1;
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
        }}

        h1 {{
            font-family: 'Anton', sans-serif;
            font-size: 3.5rem;
            text-align: center;
            color: white;
            text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            margin-bottom: 10px;
            letter-spacing: 2px;
            background: linear-gradient(45deg, #fff, #e0e7ff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            font-size: 1.2rem;
            color: #94a3b8;
            max-width: 600px;
            margin: 0 auto;
        }}

        .card-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        @media (max-width: 900px) {{
            .card-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .card {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        }}

        .card-title {{
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #e2e8f0;
            display: flex;
            align-items: center;
        }}

        .card-title i {{
            margin-right: 10px;
            font-size: 1.8rem;
        }}

        .summary-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 15px;
            overflow: hidden;
        }}

        .summary-table th,
        .summary-table td {{
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .summary-table th {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(147, 51, 234, 0.3));
            color: white;
            font-weight: 600;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-table td {{
            color: rgba(255, 255, 255, 0.9);
            font-weight: 400;
            font-size: 1rem;
        }}

        .metric-name {{
            font-weight: 600;
            color: rgba(255, 255, 255, 0.95);
        }}

        .metric-value {{
            font-weight: 300;
            color: rgba(255, 255, 255, 0.8);
        }}

        .recommendation-row {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2));
        }}

        .recommendation-row.danger {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
        }}

        .recommendation-value {{
            font-weight: 600;
            font-size: 1.1rem;
        }}

        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }}

        .status-safe {{
            background: linear-gradient(45deg, #10b981, #34d399);
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }}

        .status-danger {{
            background: linear-gradient(45deg, #ef4444, #f87171);
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
        }}

        /* Timeline visualization */
        .timeline-container {{
            margin-top: 20px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 10px;
            padding: 20px;
        }}

        .timeline-title {{
            margin-bottom: 15px;
            font-size: 1.2rem;
            color: #e2e8f0;
        }}

        .timeline {{
            display: flex;
            height: 40px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .timeline-segment {{
            position: relative;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}

        .timeline-segment:hover {{
            transform: scale(1.05);
            z-index: 2;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
        }}

        .timeline-label {{
            font-size: 0.8rem;
            font-weight: 600;
            color: white;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0 5px;
        }}

        /* State history table */
        .history-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 15px;
            overflow: hidden;
        }}

        .history-table th,
        .history-table td {{
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .history-table th {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
            color: white;
            font-weight: 600;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #94a3b8;
            font-size: 0.9rem;
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2.5rem;
            }}
            
            .container {{
                padding: 20px 15px;
            }}
            
            .card {{
                padding: 20px;
            }}
            
            .summary-table th,
            .summary-table td,
            .history-table th,
            .history-table td {{
                padding: 12px 15px;
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>DROWSINESS DETECTION SUMMARY</h1>
            <p class="subtitle">Detailed analysis of your activity and sleep patterns during the session</p>
        </header>
        
        <div class="card-grid">
            <div class="card">
                <h2 class="card-title">Session Overview</h2>
                <table class="summary-table">
                    <tbody>
                        <tr>
                            <td class="metric-name">Session Duration</td>
                            <td class="metric-value">{session_duration/60:.1f} minutes</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Total Blinks</td>
                            <td class="metric-value">{total_blinks}</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Average Blink Rate</td>
                            <td class="metric-value">{final_blink_rate:.1f} blinks/minute</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Microsleep Episodes</td>
                            <td class="metric-value">{microsleep_counter}</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Final Sleepiness</td>
                            <td class="metric-value">{sleep_percentage:.1f}%</td>
                        </tr>
                        <tr class="recommendation-row {'danger' if sleep_percentage > 50 or microsleep_counter > 0 else ''}">
                            <td class="metric-name">
                                <span class="status-indicator {'status-danger' if sleep_percentage > 50 or microsleep_counter > 0 else 'status-safe'}"></span>
                                Recommendation
                            </td>
                            <td class="recommendation-value">{recommendation}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="card">
                <h2 class="card-title">Activity Timeline</h2>
                <div class="timeline-container">
                    <div class="timeline-title">Your activity during the session:</div>
                    <div class="timeline">
                        {timeline_html}
                    </div>
                </div>
                
                <div class="legend">
                    <div style="display: flex; gap: 20px; margin-top: 20px;">
                        <div style="display: flex; align-items: center;">
                            <div style="width: 20px; height: 20px; background: #10B981; border-radius: 4px; margin-right: 8px;"></div>
                            <span>Active</span>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <div style="width: 20px; height: 20px; background: #F59E0B; border-radius: 4px; margin-right: 8px;"></div>
                            <span>Drowsy</span>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <div style="width: 20px; height: 20px; background: #EF4444; border-radius: 4px; margin-right: 8px;"></div>
                            <span>Sleeping</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 class="card-title">Detailed Activity History</h2>
            <table class="history-table">
                <thead>
                    <tr>
                        <th>State</th>
                        <th>Start Time</th>
                        <th>End Time</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
                    {state_table_html}
                </tbody>
            </table>
        </div>
        
        <footer>
            <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Drowsiness Detection System</p>
        </footer>
    </div>
</body>
</html>
""")
        
        # Clean up
        video_capture.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
