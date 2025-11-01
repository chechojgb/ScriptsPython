import os
import sys
from pathlib import Path

class Config:
    @staticmethod
    def get_base_dir():
        """Obtiene el directorio base correcto para desarrollo y producción"""
        try:
            if getattr(sys, 'frozen', False):
                # Ejecutable empaquetado - usar misma carpeta del .exe
                base_dir = Path(sys.executable).parent
            else:
                # Modo desarrollo
                base_dir = Path(os.getcwd())
            
            print(f"Directorio base: {base_dir}")
            return base_dir
        except Exception as e:
            print(f"Error obteniendo directorio base: {e}")
            return Path(".")  # Fallback al directorio actual
    
    
    DB_PATH = str(get_base_dir() / "../data" / "productivity.db")
    
    # Modo debug
    DEBUG = True