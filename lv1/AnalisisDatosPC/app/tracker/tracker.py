from app.tracker.active_window import get_active_app
from app.database.activity_repo import  save_activity
import time
from datetime import datetime, date

def track_activity():
    previous_app = get_active_app() 
    start_time = datetime.now()
    date_today = date.today()
    
    while  True:
        app_name = get_active_app() 
        if app_name != previous_app:
            print(f"Cambio detectado: {previous_app} → {app_name}")
            end_time = datetime.now()
            duration = round((end_time - start_time).total_seconds())
            
            start_hour = start_time.strftime("%H:%M:%S")
            end_hour = end_time.strftime("%H:%M:%S")
            # ejecutar la funcion de guardar en bd
            save_activity(previous_app, start_hour, end_hour, duration, date_today)
            
            # resetear los datos
            previous_app = app_name
            start_time = datetime.now()
            date_today = date.today()
        time.sleep(5)
            
        
        

