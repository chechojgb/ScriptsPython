from app.database.connection import get_connection

def save_activity(app_name, start_time, end_time, duration, date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO activities (app_name, start_time, end_time, duration, date) VALUES (?,?,?,?,?);",
                   (app_name,start_time,end_time,duration,date))
    print("Actividad guardada correctamente:",app_name)
    conn.commit()
    conn.close()    