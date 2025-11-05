#!/usr/bin/env python3
"""
Drowsiness → Arduino bridge
Every 3 sec: read JSON → extract sleep_percentage → smooth → send Pxxx
"""

import serial, time, json, sys, argparse, logging
from pathlib import Path
from typing import Optional
from serial.tools import list_ports
import os 
from pathlib import Path

# Get the directory of the currently executing script (arduino.py in the IO folder)
SCRIPT_DIR = Path(__file__).resolve().parent

# Go up one level (..) from IO and into JSON
JSON_SUBDIR = SCRIPT_DIR.parent / 'JSON'
JSON_FILE = JSON_SUBDIR / 'sleep_detection_data.json'
BAUD_RATE = 9600
POLL_SEC= 3.0 # ← 3-second cycle
SMOOTHING_ALPHA = 0.7


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# ------------------------------------------------------------------
def find_arduino_port() -> Optional[str]:
    """Auto-detect Arduino port."""
    for p in list_ports.comports():
        desc = p.description.lower()
        if 'arduino' in desc or 'usb serial' in desc:
            return p.device
    return None

# ------------------------------------------------------------------
def open_serial(port: Optional[str]) -> serial.Serial:
    """Open serial connection with auto-detect."""
    if port is None:
        port = find_arduino_port()
        if not port:
            log.error("No Arduino port auto-detected. Use --port.")
            sys.exit(1)
        log.info(f"Auto-selected port {port}")

    ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
    time.sleep(2)  # Arduino reset delay
    log.info(f"Connected to {ser.port}")
    return ser

# ------------------------------------------------------------------
# ------------------------------------------------------------------
def load_sleep_percentage() -> int:
    """
    Read JSON, extract 'sleep_percentage' from first valid driver.
    Returns 0 if missing or invalid.
    """
    # FIX 2A: Use the corrected JSON_FILE path check
    if not JSON_FILE.is_file():
        # Only log a warning if the file is genuinely missing
        log.warning(f"JSON file not found at {JSON_FILE.resolve()}") 
        return 0

    try:
        # FIX 2B: Correctly read the text from the Path object
        data = json.loads(JSON_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        log.warning(f"JSON decode error: {e}")
        return 0
    except Exception as e:
        log.error(f"File read error: {e}")
        return 0

    # Support single object or list
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        log.warning("JSON root is not list or dict")
        return 0

    for v in data:
        if not isinstance(v, dict):
            continue
            
        status = v.get('status', '').lower()
        
        # --- FIX 3: REMOVED the 'if "not running" in status: continue' block.
        # Now, it processes the percentage regardless of the status.

        sp = v.get('sleep_percentage')
        if isinstance(sp, (int, float)):
            pct = min(max(float(sp), 0), 100)
            driver_id = v.get('id', 'unknown')
            
            # Log the status that was read along with the percentage
            log.info(f"Extracted sleep_percentage = {pct}% | Status: {status} | From {driver_id}") 
            
            return round(pct)

    log.debug("No driver with sleep_percentage key found.")
    return 0
# ------------------------------------------------------------------

# ------------------------------------------------------------------
def format_cmd(pct: int) -> bytes:
    return f"P{pct:03d}".encode('ascii')

# ------------------------------------------------------------------
def main(port_arg: Optional[str]):
    ser = open_serial(port_arg)
    displayed = 0
    last_sent = -1

    log.info(f"Starting 3-second JSON read cycle (Ctrl-C to quit)")

    try:
        while True:
            start_time = time.time()

            # === 1. READ JSON ONCE ===
            current_pct = load_sleep_percentage()  # ← temp variable

            # === 2. SMOOTH & SEND ===
            displayed = int(round(displayed + SMOOTHING_ALPHA * (current_pct - displayed)))

            if displayed != last_sent:
                cmd = format_cmd(displayed)
                ser.write(cmd)
                ser.flush()
                level = round(displayed / 100 * 7)
                log.info(f"Raw:{current_pct:3d}% → Disp:{displayed:3d}%  Lvl:{level}/7  → {cmd!r}")
                last_sent = displayed
            else:
                log.debug(f"No change → still {displayed}%")

            # === 3. WAIT ~3 SECONDS ===
            elapsed = time.time() - start_time
            remaining = POLL_SEC - elapsed
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        log.info("Shutting down...")
    except serial.SerialException as e:
        log.error(f"Serial error: {e}")
    finally:
        ser.write(b'P000')
        ser.close()
        log.info("Serial closed - all LEDs off")

# ------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Drowsiness → Arduino bridge")
    parser.add_argument('-p', '--port', help='Serial port (e.g. COM3)')
    parser.add_argument('--poll', type=float, default=POLL_SEC,
                        help='Polling interval in seconds (default: 3.0)')
    args = parser.parse_args()

    POLL_SEC = args.poll  # ← no global needed

    main(args.port)