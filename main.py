import multiprocessing
import os

def run_sleep_detector():
    # Execute the file as a separate Python interpreter process
    os.system("python sleep_detector.py") 

def run_app():
    os.system("python .\web\\app.py")

def run_display():
    # Remember to include your port argument!
    os.system("python .\IoT\display.py")

if __name__ == '__main__':
    print("Starting all components in the same terminal...")
    
    # 1. Start the processes
    p1 = multiprocessing.Process(target=run_sleep_detector)
    p2 = multiprocessing.Process(target=run_app)
    p3 = multiprocessing.Process(target=run_display)

    p1.start()
    p2.start()
    p3.start()

    # 2. Wait for all processes to finish (optional)
    p1.join()
    p2.join()
    p3.join()

    print("All components shut down.")