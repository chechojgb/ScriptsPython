from fastapi import APIRouter, Depends
from app.database.connection import get_db_connection
from datetime import datetime

router = APIRouter()

@router.get("/api/real-time")
async def get_real_time_data():
    """Datos en tiempo real para el dashboard"""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}
    
    try:
        cursor = conn.cursor()
        
        # Última actividad registrada - TABLA CORRECTA: activities
        cursor.execute("""
            SELECT app_name, start_time, date 
            FROM activities 
            ORDER BY start_time DESC 
            LIMIT 1
        """)
        current_activity = cursor.fetchone()
        
        # Última actividad web - TABLA CORRECTA: web_activities
        cursor.execute("""
            SELECT site_name, start_time, date 
            FROM web_activities 
            ORDER BY start_time DESC 
            LIMIT 1
        """)
        current_web_activity = cursor.fetchone()
        
        # Estadísticas del día actual - AMBAS TABLAS
        today = datetime.now().date().isoformat()
        
        # Actividades de aplicaciones hoy
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT app_name) as app_count,
                COUNT(*) as total_entries,
                SUM(duration) as total_seconds
            FROM activities 
            WHERE date = ?
        """, (today,))
        daily_stats = cursor.fetchone()
        
        # Actividades web hoy
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT site_name) as site_count,
                COUNT(*) as total_entries,
                SUM(duration) as total_seconds
            FROM web_activities 
            WHERE date = ?
        """, (today,))
        web_stats = cursor.fetchone()
        
        # Top 5 aplicaciones hoy
        cursor.execute("""
            SELECT app_name, SUM(duration) as total_seconds
            FROM activities 
            WHERE date = ?
            GROUP BY app_name 
            ORDER BY total_seconds DESC 
            LIMIT 5
        """, (today,))
        top_apps = cursor.fetchall()
        
        # Top 5 sitios web hoy
        cursor.execute("""
            SELECT site_name, SUM(duration) as total_seconds
            FROM web_activities 
            WHERE date = ?
            GROUP BY site_name 
            ORDER BY total_seconds DESC 
            LIMIT 5
        """, (today,))
        top_sites = cursor.fetchall()
        
        return {
            "currentActivity": dict(current_activity) if current_activity else {
                "app_name": "No activity",
                "start_time": datetime.now().isoformat(),
                "date": today
            },
            "currentWebActivity": dict(current_web_activity) if current_web_activity else {
                "site_name": "No web activity",
                "start_time": datetime.now().isoformat(), 
                "date": today
            },
            "dailyStats": {
                "app_count": daily_stats["app_count"] if daily_stats else 0,
                "total_app_entries": daily_stats["total_entries"] if daily_stats else 0,
                "total_app_time": f"{(daily_stats['total_seconds'] or 0) / 3600:.2f}h",
                "site_count": web_stats["site_count"] if web_stats else 0,
                "total_web_entries": web_stats["total_entries"] if web_stats else 0,
                "total_web_time": f"{(web_stats['total_seconds'] or 0) / 3600:.2f}h"
            },
            "topApps": [dict(app) for app in top_apps],
            "topSites": [dict(site) for site in top_sites],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error en consulta: {e}"}
    finally:
        conn.close()


