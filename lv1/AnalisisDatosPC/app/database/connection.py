import sqlite3 
from app.config import Config

def get_connection():

    conn = sqlite3.connect(Config.DB_PATH)
    return conn 

def init_db():

    
    
    conn = get_connection()
    cursor = conn.cursor()

    conn.commit()
    conn.close()