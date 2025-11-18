from app.database.connection import get_connection
from datetime import datetime, date
import sqlite3

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


def safe_page_navegator(browser, site_name, start_time, end_time, duration, date, status):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO web_activities (browser, site_name, start_time, end_time, duration, date,status) VALUES (?,?,?,?,?,?,?);",
                   (browser, site_name, start_time, end_time, duration, date, status))
    print(f"Guardado web activies {browser}, {site_name} ")
    conn.commit()
    conn.close()
    
    
def create_base_category():
    
    # categories = ['comunication', 'social', 'entertainment', 'browsing', 'development', 'education', 'shopping', 'news', 'healt', 'productivity', 'adult', 'others']
    conn = get_connection()
    cursor = conn.cursor()
    
    
    
    cursor.execute('''
                   INSERT INTO categories (category) VALUES ('Communication'),('Social'), ('Entertainment'), ('Navigation'), ('Work/Development'), ('Education'), ('Shopping/Finance'), ('News'), ('Health/Wellness'), ('Productivity'), ('Adult'), ('Other');
                   ''')
    conn.commit()
    conn.close()     

def view_domain(domain: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT category_id FROM domain_category_map WHERE domain = ?;
    ''', (domain,))
    
    result = cursor.fetchone()
    conn.close()

    # Si existe, devuelve category_id; sino None
    return result[0] if result else None

def save_domain_category(domain: str, category_id: int):
    try:
        conn = get_connection()
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")

        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO domain_category_map (domain, category_id) VALUES (?, ?)",
                (domain, category_id)
            )

    except sqlite3.Error as e:
        print(f"❌ Error guardando dominio '{domain}': {e}")

    finally:
        conn.close()
    
    
