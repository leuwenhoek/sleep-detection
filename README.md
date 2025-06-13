# sleep-detection

Drowsiness Detection System
About
The Drowsiness Detection System is a real-time application designed to monitor and detect signs of drowsiness in individuals, particularly useful for drivers or those performing critical tasks. It uses computer vision techniques to analyze eye aspect ratio (EAR), head pose, and blink patterns to determine the user's alertness level. The system provides visual and auditory alerts when drowsiness or microsleep episodes are detected, and generates a detailed session summary in HTML format.
Key Features

Real-Time Drowsiness Detection: Monitors eye closure using the Eye Aspect Ratio (EAR) to detect drowsy or sleeping states.
Head Pose Estimation: Tracks head orientation (pitch, yaw, roll) to provide additional context for alertness.
Blink Rate Analysis: Calculates blink frequency and detects microsleep episodes based on prolonged eye closure.
Customizable Thresholds: Allows users to adjust EAR thresholds, save them with custom names, and load previously saved thresholds.
Session Summary: Generates a comprehensive HTML report with metrics like session duration, total blinks, blink rate, microsleep episodes, sleepiness percentage, and a timeline of activity states.
Interactive UI: Features buttons for adjusting thresholds, saving/loading settings, and a menu for managing saved thresholds.

Installation
Prerequisites

Python 3.8 or higher
Webcam (built-in or external)
Required Python packages:
opencv-python (cv2)
mediapipe
numpy



Setup

Clone the Repository:
git clone https://github.com/your-username/drowsiness-detection-system.git
cd drowsiness-detection-system


Install Dependencies:Create a virtual environment (optional but recommended) and install the required packages:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install opencv-python mediapipe numpy


Run the Application:Execute the main script:
python sleep_detector.py



Usage

Starting the Application:

Run sleep_detector.py to launch the application.
A webcam feed will open in a window titled "Real-Time Eye State Detection".
The terminal will display status messages and clear automatically after 50 messages.


Interacting with the UI:

Threshold Adjustment:
Thresh+: Increase the EAR threshold by 0.01.
Thresh-: Decrease the EAR threshold by 0.01 (minimum 0.01).
Custom: Enter a custom EAR threshold (0 to 1) via keyboard input.
Save: Save the current threshold with a custom name.
Load: Open a menu to select, edit, or delete saved thresholds.


Input Modes:
In Custom or Save modes, type the threshold value or name, then press Enter to confirm or Esc to cancel.
In the Load menu, click a threshold to apply it, "Edit" to modify its value, or "Del" to delete it.


Quit: Press 'q' to exit the application.


Output:

The application displays real-time metrics on the video feed, including:
Current EAR value
Head pose angles (pitch, yaw, roll)
Blink rate (blinks per minute)
Sleepiness percentage
Status (Active, Drowsy, Sleeping)


Alerts are triggered for high sleepiness levels (>50%) or microsleep episodes.
A session_summary.html file is generated upon exit, containing a detailed report with a timeline and state history.



File Structure

sleep_detector.py: Main script containing the drowsiness detection logic.
saved_thresholds.json: Stores saved EAR thresholds (created automatically if it doesn't exist).
state_history.json: Stores the history of state changes with timestamps.
session_summary.html: Generated report summarizing the session's metrics and activity timeline.

How It Works

Face Detection: Uses MediaPipe Face Mesh to detect facial landmarks.
Eye Aspect Ratio (EAR): Calculates the ratio of eye height to width to detect eye closure.
State Detection:
Active: EAR above threshold + 0.04, indicating open eyes.
Drowsy: EAR between threshold and threshold + 0.04, indicating partially closed eyes.
Sleeping: EAR below threshold for 16+ frames, indicating prolonged eye closure.


Microsleep Detection: Identifies prolonged eye closures (>30 frames) as microsleep episodes.
Sleepiness Percentage: Computes a weighted percentage based on recent states (Active: 0, Drowsy: 1, Sleeping: 2) over the last 100 frames.
Head Pose: Estimates head orientation using 3D model points and camera projection.
Session Summary: Records state changes with timestamps and generates an HTML report with visualizations.

Limitations

Requires a well-lit environment and a clear view of the face for accurate detection.
May not work well with glasses, heavy makeup, or occlusions.
Performance depends on webcam quality and system processing power.
No audio alert implementation (currently prints "ALERT: Wake up!" to the terminal).

Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Make your changes and commit (git commit -m "Add your feature").
Push to the branch (git push origin feature/your-feature).
Open a Pull Request.

License
This project is not licensed. Please contact the project owner for permission to use, modify, or distribute the code.
Contact
For questions or issues, please open an issue on GitHub or contact [ninjabeastyy24@gmail.com].

Generated on June 13, 2025, by the Drowsiness Detection System.

