from fastapi import APIRouter, Depends
from app.database.connection import get_db_connection
from app.config import Config
import os
from datetime import datetime

router = APIRouter()
    
@router.get("/api/status")
async def get_system_status():
    """Estado del sistema para el frontend"""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}
    
    try:
        
        return {
            "status": "online",
            "database": {
                "path": Config.DB_PATH,
                "exists": os.path.exists(Config.DB_PATH)
            },
            "server": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.1"
            }
        }
    except Exception as e:
        return {"error": f"Error en consulta: {e}"}
    finally:
        conn.close()

