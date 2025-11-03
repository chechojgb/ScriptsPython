# main.py (compilado como ActivityTracker.exe SIN consola)
import os
import sys
import time
import logging
from datetime import datetime

# Configurar logging
log_path = os.path.join(os.path.expanduser("~"), "Documents", "trackerk.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def main():
    try:
        logging.info("TrackerK ejecutándose en segundo plano - %s", 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        from app.database.connection import init_db
        from app.tracker.tracker import start_tracking
        
        # Inicializar BD
        init_db()
        logging.info("Base de datos lista")
        
        # Iniciar tracking infinito
        start_tracking()
        
    except Exception as e:
        logging.error(f"Error crítico: {e}")
        time.sleep(5)  # Esperar antes de cerrar para ver el error

if __name__ == "__main__":
    main()