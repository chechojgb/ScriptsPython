# tracker_main.py
import os
import sys
import time
import logging
from datetime import datetime

# Configurar logging para verificar que funciona
log_path = os.path.join(os.path.expanduser("~"), "Documents", "trackerk.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def main():
    try:
        logging.info("=== TRACKERK INICIADO EN SEGUNDO PLANO ===")
        
        # Agregar ruta de la aplicación al path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from app.database.connection import init_db
        from app.tracker.tracker import start_tracking
        
        logging.info("Importando módulos...")
        
        # Inicializar base de datos
        init_db()
        logging.info("Base de datos inicializada")
        
        # Iniciar tracking
        logging.info("Iniciando tracker...")
        start_tracking()
        
    except Exception as e:
        logging.error(f"ERROR: {str(e)}")
        # Mantener el proceso vivo para ver el error
        time.sleep(10)

if __name__ == "__main__":
    main()