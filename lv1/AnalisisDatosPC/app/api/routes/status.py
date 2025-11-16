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
        cursor = conn.cursor()
        
        # Información general - USANDO LOS NOMBRES CORRECTOS
        cursor.execute("SELECT COUNT(*) as total FROM activities")
        total_activities = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM web_activities")
        total_web = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(DISTINCT app_name) as apps FROM activities")
        unique_apps = cursor.fetchone()["apps"]
        
        return {
            "status": "online",
            "database": {
                "path": Config.DB_PATH,
                "total_activities": total_activities,
                "total_web_activities": total_web,
                "unique_apps": unique_apps,
                "exists": os.path.exists(Config.DB_PATH)
            },
            "server": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }
    except Exception as e:
        return {"error": f"Error en consulta: {e}"}
    finally:
        conn.close()

