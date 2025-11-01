from app.database.connection import init_db
from app.database.activity_repo import close_active_sessions
from app.tracker.tracker import track_activity, start_tracking
from app.config import Config
from datetime import date, datetime
import time
import os
import itertools
import sys


def mostrar_banner_trackerk():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    banner = r"""
  __                        __                     ________    _________
_/  |_____________    ____ |  | __ ___________     \_____  \  /   _____/
\   __\_  __ \__  \ _/ ___\|  |/ // __ \_  __ \     /   |   \ \_____  \ 
 |  |  |  | \// __ \\  \___|    <\  ___/|  | \/    /    |    \/        \
 |__|  |__|  (____  /\___  >__|_ \\___  >__|       \_______  /_______  /
                  \/     \/     \/    \/                   \/        \/                                 
    """
    
    print(banner)
    print("Consola segura iniciando TRACKERK OS...\n")

    spinner = itertools.cycle(['-', '\\', '|', '/'])
    for _ in range(30):
        sys.stdout.write(f"\r Ejecutando TrackerK OS {next(spinner)}")
        sys.stdout.flush()
        time.sleep(0.08)

    print("\n TrackerK OS se ha iniciado correctamente.\n")
    time.sleep(1)

# Llamar al banner antes de iniciar el rastreo

def main():
    try:
        mostrar_banner_trackerk()
        time.sleep(2)
        init_db()
        time.sleep(1)
        start_tracking()
        
    except Exception as e:
        print(f"Error crítico: {e}")
        print(f"Ruta de BD intentada: {Config.DB_PATH}")
        input("Presiona Enter para salir...")
    
if __name__ == "__main__":
    main()
