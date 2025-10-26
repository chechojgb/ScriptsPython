from app.tracker.active_window import get_active_app
from app.database.activity_repo import  save_activity, safe_page_navegator
import time
from datetime import datetime, date
import win32gui




    
    
def track_activity():
    previous_app = get_active_app() 
    start_time = datetime.now()
    date_today = date.today()
    status = "closed"
    previous_title = None
    
    while  True:
        app_name = get_active_app() 
        interval = 60
        elapsed = (datetime.now() - start_time).total_seconds()
        previous_title = track_web_activity(elapsed, app_name, start_time, date_today, status, previous_title)
        
        if app_name != previous_app:
            print(f"Cambio detectado: {previous_app} → {app_name}")
            end_time = datetime.now()
            duration = round((end_time - start_time).total_seconds())
            
            start_hour = start_time.strftime("%H:%M:%S")
            end_hour = end_time.strftime("%H:%M:%S")
            # ejecutar la funcion de guardar en bd
            save_activity(previous_app, start_hour, end_hour, duration, date_today, status)
            
            # resetear los datos
            previous_app = app_name
            start_time = datetime.now()
        elif elapsed >= interval:
            print(f"Minuto sin cambios, se guarda: {previous_app}")
            end_time = datetime.now()
            duration = round((end_time - start_time).total_seconds())
            start_hour = start_time.strftime("%H:%M:%S")
            end_hour = end_time.strftime("%H:%M:%S")
            save_activity(previous_app, start_hour, end_hour, duration, date_today, status)
            start_time = datetime.now()
            
        time.sleep(5)
    pass
        
        
        
def track_web_activity(elapsed, app_name, start_time, date_today, status, previus_title=None  ):
    interval = 60
    navegadores = ['chrome.exe', 'msedge.exe', 'opera.exe', 'firefox.exe']
    if app_name in navegadores:
        title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        if previus_title != title:    
            print("Se guarda ventana activa", title)
            end_time = datetime.now()
            duration = round((end_time-start_time).total_seconds())
            start_hour = start_time.strftime("%H:%M:%S")
            end_hour = end_time.strftime("%H:%M:%S")
            safe_page_navegator(app_name, title, start_hour, end_hour, duration, date_today, status)
            return title
        elif elapsed >= interval:
            print("Se guarda ventana activa pasado el minuto", title)
            end_time = datetime.now()
            duration = round((end_time-start_time).total_seconds())
            start_hour = start_time.strftime("%H:%M:%S")
            end_hour = end_time.strftime("%H:%M:%S")
            safe_page_navegator(app_name, title, start_hour, end_hour, duration, date_today, status)
            return title
    return previus_title
        
        
def start_tracking():
    track_activity()
    
    
            
            
        
        

