import win32gui
import win32process
import psutil

def get_active_app():
    window = win32gui.GetForegroundWindow()

    _, pid = win32process.GetWindowThreadProcessId(window)

    app_name = psutil.Process(pid).name()

    return app_name