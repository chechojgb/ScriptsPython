import os

class Config:
    # Obtiene la ruta base del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Ruta del archivo SQLite
    DB_PATH = os.path.join(BASE_DIR, "data", "productivity.db")

    # Modo debug (para desarrollo)
    DEBUG = True
