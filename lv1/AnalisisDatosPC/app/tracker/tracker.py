import win32gui
import win32process
import psutil
import time


def track_activity():
    previous_app = None
    bucle = 0
    while  True:
        nombre = get_active_app()
        if nombre != previous_app:
            print(f"Cambio detectado: {previous_app} → {nombre}")
            previous_app = nombre
        
        time.sleep(5)
            
        
        

def get_active_app():
    window = win32gui.GetForegroundWindow()

    _, pid = win32process.GetWindowThreadProcessId(window)

    app_name = psutil.Process(pid).name()

    return app_name