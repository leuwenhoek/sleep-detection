# Drowsiness Detection System  
**Real-Time Driver Monitoring with Computer Vision, Web Dashboard & Arduino Feedback**


---

## Overview
This system detects **driver drowsiness in real-time** using computer vision and provides **visual + audio + physical alerts** using **web dashboard & Arduino components**.

---

## Features

- **Real-Time Eye & Face Analysis**
  - Uses **MediaPipe Face Mesh** + **OpenCV**
  - Detects **blinks, microsleep, yawning, head tilt**

- **Sleepiness Score Calculation**
  - Tracks recent eye state to calculate **sleep percentage**

- **Live Threshold Adjustment**
  - Press `+` / `-` to adjust EAR threshold
  - Press `t` to **save/load** presets

- **Web Dashboard (Flask)**
  - View **live state**, graphs, and logs at `http://127.0.0.1:5000`

- **Arduino Alert System**
  - **7 LEDs** as **alert severity meter**
  - **OLED Display (128x32)** shows sleep level
  - Uses smoothed values (no flickering)

- **Session Summary HTML Report**
  - Generated automatically on exit

---

## Demo
| [![KZDJfcv.md.png](https://iili.io/KZDJfcv.md.png)](https://freeimage.host/i/KZDJfcv)
[![KZDJqSR.md.png](https://iili.io/KZDJqSR.md.png)](https://freeimage.host/i/KZDJqSR)

 | ![](images/dashboard.gif) | ![](images/arduino.gif) |

---

## 🛠️ Hardware Requirements

| Component | Requirement |
|---------|-------------|
| Camera | USB / Laptop Webcam |
| Arduino | Uno / Nano |
| OLED Display | SSD1306 128x32 I2C |
| LEDs | 7 LEDs + 330Ω resistors |
| Wires | Male-to-male jumper wires |

---

## 💻 Software Requirements

```bash
Python 3.8+
Arduino IDE
```

### Install Python Libraries
```bash
pip install -r requirements.txt
```

### Arduino Libraries Required
- Adafruit GFX Library
- Adafruit SSD1306

---

## 🔧 Setup & Installation

```bash
git clone https://github.com/yourusername/drowsiness-detection-system.git
cd drowsiness-detection-system

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Wiring (Summary)
```
Arduino Pin  → Component
2–8          → LEDs (+330Ω → GND)
A4 (SDA)     → OLED SDA
A5 (SCL)     → OLED SCL
5V           → OLED VCC
GND          → OLED GND & LED GND
```

Upload `sleep_monitor.ino` to Arduino.

---

## ▶️ Run the System

```bash
python main.py
```

This starts:
| File | Function |
|------|----------|
| `sleep_detector.py` | Runs detection + logs state |
| `app.py` | Web dashboard |
| `display.py` | Sends data to Arduino |

---

## 🎮 Controls (During Webcam Feed)

| Key | Action |
|-----|--------|
| `+ / -` | Increase / decrease EAR threshold |
| `t` | Threshold menu (save/load) |
| `s` | Toggle alert sound |
| `q` | Quit & generate HTML report |

---

## 📁 Project Structure

```
C:.
|   .gitignore
|   main.py
|   README.md
|   requirements.txt
|   sleep_detector.py
|   structure.txt
|
+---circuit
|       Advance.pdf
|       
+---IoT
|   |   display.py
|   |   
|   \---sleep_moniter
|           sleep_moniter.ino
|           
+---JSON
|       saved_thresholds.json
|       sleep_detection_data.json
|       state_history.json
|       
+---session
|       session_summary.html
|       
\---web
    |   app.py
    |   
    +---static
    |       style.css
    |       
    \---templates
            dashboard.html
            

```

---

## 📊 Session Summary
When you press **q**:
```
session_summary_YYYY-MM-DD_HH-MM-SS.html
```
Includes:
- Duration
- Blinks + microsleep count
- Final sleep percentage
- Timeline visualization
- Recommendations

---

## 🤝 Contributing
1. Fork repo
2. Create branch
3. Make improvements
4. Submit pull request

---

**Made with ❤️ to help prevent fatigue-related accidents.**
