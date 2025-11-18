from fastapi import APIRouter, Depends
from app.database.connection import get_db_connection
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/api/reports")
async def get_reports(
    start_date: str = None, 
    end_date: str = None,
    period: str = "complete"
):
    """Reportes históricos flexibles por período"""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}
    
    try:
        cursor = conn.cursor()
        
        # Determinar fechas según el período
        date_range = await calculate_date_range(period, start_date, end_date)
        start_date = date_range["start_date"]
        end_date = date_range["end_date"]
        
        # Tiempo por aplicación - CON COALESCE
        cursor.execute("""
            SELECT 
                app_name as name,
                COALESCE(SUM(duration), 0) / 3600.0 as hours
            FROM activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY app_name 
            ORDER BY hours DESC
            LIMIT 10
        """, (start_date, end_date))
        apps_time = [dict(row) for row in cursor.fetchall()]
        
        # Tiempo por sitio web - CON COALESCE
        cursor.execute("""
            SELECT 
                site_name as name,
                COALESCE(SUM(duration), 0) / 3600.0 as hours 
            FROM web_activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY site_name 
            ORDER BY hours DESC
            LIMIT 10
        """, (start_date, end_date))
        sites_time = [dict(row) for row in cursor.fetchall()]
        
        # Resumen general - CON COALESCE
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT app_name) as appsTracked,
                COUNT(DISTINCT date) as daysTracked,
                COALESCE(SUM(duration), 0) / 3600.0 as totalTime 
            FROM activities 
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        app_summary = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT site_name) as sitesTracked,
                COALESCE(SUM(duration), 0) / 3600.0 as totalWebTime 
            FROM web_activities 
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))
        web_summary = cursor.fetchone()
        
        # Combinar resúmenes - CON MEJOR MANEJO DE None
        summary = {
            "appsTracked": app_summary["appsTracked"] if app_summary and app_summary["appsTracked"] is not None else 0,
            "sitesTracked": web_summary["sitesTracked"] if web_summary and web_summary["sitesTracked"] is not None else 0,
            "daysTracked": app_summary["daysTracked"] if app_summary and app_summary["daysTracked"] is not None else 0,
            "totalAppTime": app_summary["totalTime"] if app_summary and app_summary["totalTime"] is not None else 0,
            "totalWebTime": web_summary["totalWebTime"] if web_summary and web_summary["totalWebTime"] is not None else 0,
            "totalTime": (app_summary["totalTime"] if app_summary and app_summary["totalTime"] is not None else 0) + 
                        (web_summary["totalWebTime"] if web_summary and web_summary["totalWebTime"] is not None else 0)
        }
        
        return {
            "appsTime": apps_time,
            "sitesTime": sites_time,
            "summary": summary,
            "dateRange": f"{start_date} to {end_date}",
            "period": period
        }
        
    except Exception as e:
        return {"error": f"Error generando reportes: {e}"}
    finally:
        conn.close()

async def calculate_date_range(period: str, start_date: str = None, end_date: str = None):
    """Calcula el rango de fechas según el período"""
    today = datetime.now().date()
    
    # Mejor manejo de valores None/empty
    if start_date and end_date and start_date != "null" and end_date != "null":
        return {"start_date": start_date, "end_date": end_date}
    
    if period == "daily":
        start = today
        end = today
    elif period == "weekly":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif period == "monthly":
        start = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end = next_month - timedelta(days=next_month.day)
    else:  # "complete"
        start = "2020-01-01"
        end = today
    
    return {
        "start_date": start.isoformat() if hasattr(start, 'isoformat') else start,
        "end_date": end.isoformat() if hasattr(end, 'isoformat') else end
    }