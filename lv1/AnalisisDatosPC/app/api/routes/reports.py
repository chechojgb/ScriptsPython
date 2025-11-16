from fastapi import APIRouter, Depends
from app.database.connection import get_db_connection

router = APIRouter()

    
@router.get("/api/reports")
async def get_reports(start_date: str, end_date: str):
    """Reportes históricos para la página de reports"""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}
    
    try:
        cursor = conn.cursor()
        
        # Tiempo por aplicación - TABLA CORRECTA: activities
        cursor.execute("""
            SELECT 
                app_name as name,
                SUM(duration) / 3600.0 as hours
            FROM activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY app_name 
            ORDER BY hours DESC
            LIMIT 10
        """, (start_date, end_date))
        apps_time = [dict(row) for row in cursor.fetchall()]
        
        # Tiempo por sitio web - TABLA CORRECTA: web_activities
        cursor.execute("""
            SELECT 
                site_name as name,
                SUM(duration) / 3600.0 as hours
            FROM web_activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY site_name 
            ORDER BY hours DESC
            LIMIT 10
        """, (start_date, end_date))
        sites_time = [dict(row) for row in cursor.fetchall()]
        
        # Resumen general - COMBINANDO AMBAS TABLAS
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT app_name) as appsTracked,
                COUNT(DISTINCT date) as daysTracked,
                SUM(duration) / 3600.0 as totalTime
            FROM activities 
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        app_summary = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT site_name) as sitesTracked,
                SUM(duration) / 3600.0 as totalWebTime
            FROM web_activities 
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        web_summary = cursor.fetchone()
        
        # Combinar resúmenes
        summary = {
            "appsTracked": app_summary["appsTracked"] if app_summary else 0,
            "sitesTracked": web_summary["sitesTracked"] if web_summary else 0,
            "daysTracked": app_summary["daysTracked"] if app_summary else 0,
            "totalAppTime": app_summary["totalTime"] if app_summary else 0,
            "totalWebTime": web_summary["totalWebTime"] if web_summary else 0,
            "totalTime": (app_summary["totalTime"] if app_summary else 0) + 
                        (web_summary["totalWebTime"] if web_summary else 0)
        }
        
        return {
            "appsTime": apps_time,
            "sitesTime": sites_time,
            "summary": summary,
            "dateRange": f"{start_date} to {end_date}"
        }
        
    except Exception as e:
        return {"error": f"Error generando reportes: {e}"}
    finally:
        conn.close()
