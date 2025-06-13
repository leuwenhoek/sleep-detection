<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drowsiness Detection System - README</title>
</head>
<body>
    <h1>Drowsiness Detection System</h1>

    <h2>About</h2>
    <p>The Drowsiness Detection System is a real-time application designed to monitor and detect signs of drowsiness in individuals, particularly useful for drivers or those performing critical tasks. It uses computer vision techniques to analyze eye aspect ratio (EAR), head pose, and blink patterns to determine the user's alertness level. The system provides visual and auditory alerts when drowsiness or microsleep episodes are detected, and generates a detailed session summary in HTML format.</p>

    <h3>Key Features</h3>
    <ul>
        <li><strong>Real-Time Drowsiness Detection</strong>: Monitors eye closure using the Eye Aspect Ratio (EAR) to detect drowsy or sleeping states.</li>
        <li><strong>Head Pose Estimation</strong>: Tracks head orientation (pitch, yaw, roll) to provide additional context for alertness.</li>
        <li><strong>Blink Rate Analysis</strong>: Calculates blink frequency and detects microsleep episodes based on prolonged eye closure.</li>
        <li><strong>Customizable Thresholds</strong>: Allows users to adjust EAR thresholds, save them with custom names, and load previously saved thresholds.</li>
        <li><strong>Session Summary</strong>: Generates a comprehensive HTML report with metrics like session duration, total blinks, blink rate, microsleep episodes, sleepiness percentage, and a timeline of activity states.</li>
        <li><strong>Interactive UI</strong>: Features buttons for adjusting thresholds, saving/loading settings, and a menu for managing saved thresholds.</li>
    </ul>

    <h2>Installation</h2>

    <h3>Prerequisites</h3>
    <ul>
        <li>Python 3.8 or higher</li>
        <li>Webcam (built-in or external)</li>
        <li>Required Python packages:
            <ul>
                <li><code>opencv-python</code> (<code>cv2</code>)</li>
                <li><code>mediapipe</code></li>
                <li><code>numpy</code></li>
            </ul>
        </li>
    </ul>

    <h3>Setup</h3>
    <ol>
        <li><strong>Clone the Repository</strong>:
            <pre><code>git clone https://github.com/your-username/drowsiness-detection-system.git
cd drowsiness-detection-system</code></pre>
        </li>
        <li><strong>Install Dependencies</strong>:
            <p>Create a virtual environment (optional but recommended) and install the required packages:</p>
            <pre><code>python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install opencv-python mediapipe numpy</code></pre>
        </li>
        <li><strong>Run the Application</strong>:
            <p>Execute the main script:</p>
            <pre><code>python sleep_detector.py</code></pre>
        </li>
    </ol>

    <h2>Usage</h2>

    <ol>
        <li><strong>Starting the Application</strong>:
            <p>Run <code>sleep_detector.py</code> to launch the application. A webcam feed will open in a window titled "Real-Time Eye State Detection". The terminal will display status messages and clear automatically after 50 messages.</p>
        </li>
        <li><strong>Interacting with the UI</strong>:
            <ul>
                <li><strong>Threshold Adjustment</strong>:
                    <ul>
                        <li><strong>Thresh+</strong>: Increase the EAR threshold by 0.01.</li>
                        <li><strong>Thresh-</strong>: Decrease the EAR threshold by 0.01 (minimum 0.01).</li>
                        <li><strong>Custom</strong>: Enter a custom EAR threshold (0 to 1) via keyboard input.</li>
                        <li><strong>Save</strong>: Save the current threshold with a custom name.</li>
                        <li><strong>Load</strong>: Open a menu to select, edit, or delete saved thresholds.</li>
                    </ul>
                </li>
                <li><strong>Input Modes</strong>:
                    <ul>
                        <li>In Custom or Save modes, type the threshold value or name, then press Enter to confirm or Esc to cancel.</li>
                        <li>In the Load menu, click a threshold to apply it, "Edit" to modify its value, or "Del" to delete it.</li>
                    </ul>
                </li>
                <li><strong>Quit</strong>: Press 'q' to exit the application.</li>
            </ul>
        </li>
        <li><strong>Output</strong>:
            <p>The application displays real-time metrics on the video feed, including:</p>
            <ul>
                <li>Current EAR value</li>
                <li>Head pose angles (pitch, yaw, roll)</li>
                <li>Blink rate (blinks per minute)</li>
                <li>Sleepiness percentage</li>
                <li>Status (Active, Drowsy, Sleeping)</li>
            </ul>
            <p>Alerts are triggered for high sleepiness levels (>50%) or microsleep episodes. A <code>session_summary.html</code> file is generated upon exit, containing a detailed report with a timeline and state history.</p>
        </li>
    </ol>

    <h2>File Structure</h2>
    <ul>
        <li><code>sleep_detector.py</code>: Main script containing the drowsiness detection logic.</li>
        <li><code>saved_thresholds.json</code>: Stores saved EAR thresholds (created automatically if it doesn't exist).</li>
        <li><code>state_history.json</code>: Stores the history of state changes with timestamps.</li>
        <li><code>session_summary.html</code>: Generated report summarizing the session's metrics and activity timeline.</li>
    </ul>

    <h2>How It Works</h2>
    <ol>
        <li><strong>Face Detection</strong>: Uses MediaPipe Face Mesh to detect facial landmarks.</li>
        <li><strong>Eye Aspect Ratio (EAR)</strong>: Calculates the ratio of eye height to width to detect eye closure.</li>
        <li><strong>State Detection</strong>:
            <ul>
                <li><strong>Active</strong>: EAR above threshold + 0.04, indicating open eyes.</li>
                <li><strong>Drowsy</strong>: EAR between threshold and threshold + 0.04, indicating partially closed eyes.</li>
                <li><strong>Sleeping</strong>: EAR below threshold for 16+ frames, indicating prolonged eye closure.</li>
            </ul>
        </li>
        <li><strong>Microsleep Detection</strong>: Identifies prolonged eye closures (>30 frames) as microsleep episodes.</li>
        <li><strong>Sleepiness Percentage</strong>: Computes a weighted percentage based on recent states (Active: 0, Drowsy: 1, Sleeping: 2) over the last 100 frames.</li>
        <li><strong>Head Pose</strong>: Estimates head orientation using 3D model points and camera projection.</li>
        <li><strong>Session Summary</strong>: Records state changes with timestamps and generates an HTML report with visualizations.</li>
    </ol>

    <h2>Limitations</h2>
    <ul>
        <li>Requires a well-lit environment and a clear view of the face for accurate detection.</li>
        <li>May not work well with glasses, heavy makeup, or occlusions.</li>
        <li>Performance depends on webcam quality and system processing power.</li>
        <li>No audio alert implementation (currently prints "ALERT: Wake up!" to the terminal).</li>
    </ul>

    <h2>Contributing</h2>
    <p>Contributions are welcome! To contribute:</p>
    <ol>
        <li>Fork the repository.</li>
        <li>Create a new branch (<code>git checkout -b feature/your-feature</code>).</li>
        <li>Make your changes and commit (<code>git commit -m "Add your feature"</code>).</li>
        <li>Push to the branch (<code>git push origin feature/your-feature</code>).</li>
        <li>Open a Pull Request.</li>
    </ol>

    <h2>License</h2>
    <p>This project is not licensed. Please contact the project owner for permission to use, modify, or distribute the code.</p>

    <h2>Contact</h2>
    <p>For questions or issues, please open an issue on GitHub or contact <a href="mailto:your-email@example.com">your-email@example.com</a>.</p>

    <hr>
    <p><em>Generated on June 13, 2025, by the Drowsiness Detection System.</em></p>
</body>
</html>