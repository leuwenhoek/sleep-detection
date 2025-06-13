# Drowsiness Detection System

## Overview

The **Drowsiness Detection System** is an *advanced real-time application* engineered to detect and monitor signs of drowsiness, particularly for individuals engaged in safety-critical tasks such as driving or operating machinery. It leverages computer vision techniques, analyzing the **Eye Aspect Ratio (EAR)**, head pose, and blink patterns to assess alertness levels.

### Key Features

- **Real-Time Drowsiness Detection**: Continuously monitors eye closure via EAR
- **Head Pose Estimation**: Tracks head orientation (pitch, yaw, roll)
- **Blink Rate Analysis**: Calculates blink frequency and identifies microsleep episodes
- **Customizable Thresholds**: Adjustable EAR thresholds via interactive UI
- **Session Summary**: Generates comprehensive HTML reports
- **Interactive User Interface**: Real-time video feed with control buttons

## Installation

### Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python Version** | 3.8 or higher |
| **Hardware** | Functional webcam (integrated or external) |
| **Required Packages** | `opencv-python`, `mediapipe`, `numpy` |

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/drowsiness-detection-system.git
   cd drowsiness-detection-system
   ```
   *Note: Replace `your-username` with the actual GitHub username*

2. **Create Virtual Environment** *(Recommended)*
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install opencv-python mediapipe numpy
   ```

4. **Run the Application**
   ```bash
   python sleep_detector.py
   ```

## Usage

### Starting the Application

Execute the main script to launch the system:

```bash
python sleep_detector.py
```

The application will open a window titled *"Real-Time Eye State Detection"* displaying your webcam feed.

### User Interface Controls

#### Threshold Adjustment
- **Thresh+**: Increase EAR threshold by 0.01
- **Thresh-**: Decrease EAR threshold by 0.01
- **Custom**: Enter custom threshold value (0 to 1)
- **Save**: Save current threshold with custom name
- **Load**: Load previously saved thresholds

#### Real-time Metrics Display
- Current **EAR** value
- Head pose angles (*pitch, yaw, roll*)
- Blink rate (blinks per minute)
- Sleepiness percentage
- Current status: `Active :)`, `Drowsy !`, or `SLEEPING !!!`

### Exiting the Application

Press `q` to quit the application. This will automatically generate a **session summary** in HTML format.

## File Structure

```
drowsiness-detection-system/
├── sleep_detector.py          # Main application script
├── saved_thresholds.json      # User-defined EAR thresholds
├── state_history.json         # Session state transitions
├── session_summary.html       # Generated session report
└── README.md                  # This file
```

## Technical Details

### Detection States

The system classifies alertness into three states:

1. **Active** (`EAR > threshold + 0.04`): *Fully alert state*
2. **Drowsy** (`threshold ≤ EAR < threshold + 0.04`): *Mild drowsiness detected*
3. **Sleeping** (`EAR < threshold` for 16+ frames): ***Significant drowsiness - ALERT triggered***

### Core Technologies

- **MediaPipe Face Mesh**: Facial landmark detection
- **OpenCV**: Computer vision processing
- **Eye Aspect Ratio (EAR)**: Primary drowsiness metric
- **Head Pose Estimation**: 3D orientation tracking

### Session Analytics

The system generates detailed session summaries including:
- Total session duration
- Blink count and rate
- Microsleep episodes (eye closure >30 frames)
- Sleepiness percentage over time
- Visual timeline of activity states
- *Personalized recommendations*

## Limitations

- Requires **well-lit environment** for optimal performance
- May have *reduced accuracy* with glasses or facial occlusions
- Performance depends on webcam quality and system resources
- Currently lacks audio alert implementation

## Contributing

We welcome contributions! To contribute:

1. **Fork** the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and commit:
   ```bash
   git commit -m "Add your feature description"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Submit a **Pull Request**

## License

This project is currently *unlicensed*. Please contact the project owner for usage permissions.

## Contact

- **Email**: ninjabeastyy24@gmail.com
- **Issues**: Open an issue on the GitHub repository
- **Support**: Contact via email for technical assistance

---

*Generated on June 13, 2025*

**⚠️ Safety Notice**: This system is designed to assist with drowsiness detection but should not be the sole safety measure in critical applications. Always prioritize proper rest and safe practices.