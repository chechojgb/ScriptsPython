# launcher.py
import subprocess
import sys
import os
import time

def mostrar_banner():
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
    
    # Spinner rápido
    import itertools
    spinner = itertools.cycle(['-', '\\', '|', '/'])
    for _ in range(12):  # ~2 segundos
        sys.stdout.write(f"\r Ejecutando TrackerK OS {next(spinner)}")
        sys.stdout.flush()
        time.sleep(0.16)
    

if __name__ == "__main__":
    mostrar_banner()
    
    # Ruta al ejecutable del tracker (sin consola)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tracker_exe = os.path.join(current_dir, "dist", "ActivityTracker.exe")
    
    if os.path.exists(tracker_exe):
        # Ejecutar el tracker SIN consola
        if os.name == 'nt':
            subprocess.Popen([tracker_exe], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen([tracker_exe],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Si no existe el .exe, ejecutar el script Python directamente
        tracker_script = os.path.join(current_dir, "tracker_main.py")
        if os.name == 'nt':
            subprocess.Popen([sys.executable, tracker_script], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen([sys.executable, tracker_script],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # CERRAR COMPLETAMENTE esta consola
    sys.exit(0)