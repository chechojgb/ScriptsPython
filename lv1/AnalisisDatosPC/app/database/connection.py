import sqlite3 
from app.config import Config

def get_connection():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn 

get_db_connection = get_connection

def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        print('Conexion exitosa')
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_name TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        duration REAL,
                        date TEXT NOT NULL,
                        status TEXT DEFAULT 'closed'
                    )
                    ''')
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS web_activities (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            browser TEXT NOT NULL,
                            site_name TEXT NOT NULL,
                            start_time TEXT NOT NULL,
                            end_time TEXT NOT NULL,
                            duration INTEGER NOT NULL,
                            date TEXT NOT NULL,
                            status TEXT DEFAULT 'closed'
                    )
                    ''')
        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS categories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            category TEXT NOT NULL UNIQUE
                        );
                       ''')
        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS domain_category_map (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            domain TEXT NOT NULL UNIQUE,
                            category_id INTEGER NOT NULL,
                            FOREIGN KEY (category_id) REFERENCES categories(id)
                        );
                       ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'Error DB {e}')
        raise
    
    