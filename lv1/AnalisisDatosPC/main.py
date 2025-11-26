# main.py
import os
import logging
import sys
from datetime import datetime
from multiprocessing import Process, freeze_support

# Configurar logging
log_path = os.path.join(os.path.expanduser("~"), "Documents", "trackerk.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def start_api():
    """Iniciar API en proceso separado - Versión robusta"""
    try:
        import sys
        import io
        import os
        
        # FIX CRÍTICO: Configurar environment para uvicorn
        os.environ["UVICORN_SERVER"] = "1"
        
        # Redirigir stdout/stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        # Configuración de logging ultra mínima
        import logging
        logging.basicConfig(level=logging.CRITICAL)  # Solo errores críticos
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        
        import uvicorn
        from app.api.api_main import app
        
        # FIX: Usar run_simple para evitar problemas de configuración
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=5000,
            log_config=None,        # NO usar configuración de log de uvicorn
            access_log=False,       # NO logs de acceso
            server_header=False,    # NO header del servidor
            date_header=False,      # NO header de fecha
            loop="asyncio"
        )
        
    except Exception as e:
        # Fallback: escribir en archivo
        try:
            import datetime
            error_path = os.path.join(os.path.expanduser("~"), "Documents", "tracker_api_errors.log")
            with open(error_path, 'a') as f:
                f.write(f"{datetime.datetime.now()} - API FAILED: {str(e)}\n")
        except:
            pass  # Si todo falla, no hacer nada

def main():
    freeze_support()
    
    logging.info("TrackerK iniciado - %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Base de datos en:",os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Inicializar base de datos
        from app.database.connection import init_db
        init_db()
        logging.info("Base de datos inicializada")
        
        # Iniciar API en proceso separado
        api_process = Process(target=start_api)
        api_process.daemon = True
        api_process.start()
        logging.info("Proceso API iniciado (PID: %s)", api_process.pid)
        
        # Pequeña pausa para que el proceso API se inicie
        import time
        time.sleep(2)
        
        # Verificar si la API está corriendo
        try:
            import requests
            response = requests.get("http://127.0.0.1:5000/docs", timeout=5)
            if response.status_code == 200:
                logging.info("✅ API confirmada funcionando en http://127.0.0.1:5000")
            else:
                logging.warning("⚠️ API responde pero con estado: %s", response.status_code)
        except:
            logging.warning("⚠️ No se pudo verificar la API, pero el proceso está ejecutándose")
        
        # Iniciar tracker
        from app.tracker.tracker import start_tracking
        logging.info("Iniciando tracker...")
        start_tracking()
        
    except Exception as e:
        logging.error(f"Error en main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()