from app.database.connection import get_connection
from datetime import datetime, date

def save_activity(app_name, start_time, end_time, duration, date,status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO activities (app_name, start_time, end_time, duration, date,status) VALUES (?,?,?,?,?,?);",
                   (app_name,start_time,end_time,duration,date,status))
    print("Actividad guardada correctamente:",app_name)
    conn.commit()
    conn.close()    


def close_active_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, start_time FROM activities WHERE status = 'active'")
    for row in cursor.fetchall():
        id = row[0]
        start_time = row[1]
        start_time_dt = datetime.strptime(start_time, "%H:%M:%S")
        end_time = datetime.now()
        duration = round((end_time-start_time_dt).total_seconds())
        status = 'closed'
        cursor.execute("UPDATE activities SET  end_time =?, duration=?, status=? WHERE id=?",(end_time.strftime("%H:%M:%S"),duration,status, id))
    
    conn.commit()
    conn.close()   
        
    
    
    
