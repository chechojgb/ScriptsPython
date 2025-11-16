from fastapi import APIRouter, Depends
from app.database.connection import get_db_connection
from datetime import datetime, timedelta

router = APIRouter()
# iniciador

@router.get("/api/weekly-changes")
async def get_weekly_changes(session_period: str = "daily"):
    """Obtiene los cambios de esta semana vs la semana anterior"""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}
    
    try:
        cursor = conn.cursor()
        
        # Definir rangos de fecha (esta semana vs semana anterior)
        today = datetime.now().date()
        start_current_week = today - timedelta(days=today.weekday())  # Lunes de esta semana
        end_current_week = start_current_week + timedelta(days=6)     # Domingo de esta semana
        
        start_previous_week = start_current_week - timedelta(days=7)  # Lunes semana anterior
        end_previous_week = start_previous_week + timedelta(days=6)   # Domingo semana anterior
        
        # 1. APPS NUEVAS ESTA SEMANA
        cursor.execute("""
            SELECT COUNT(DISTINCT app_name) as new_apps FROM activities WHERE date BETWEEN ? AND ?
            AND app_name NOT IN (
                SELECT DISTINCT app_name FROM activities WHERE date BETWEEN ? AND ?
            )
        """, (start_current_week, end_current_week, start_previous_week, end_previous_week))
        new_apps_result = cursor.fetchone()
        new_apps = new_apps_result["new_apps"] if new_apps_result and new_apps_result["new_apps"] is not None else 0
        
        # 2. SITIOS NUEVOS ESTA SEMANA
        cursor.execute("""
            SELECT COUNT(DISTINCT site_name) as new_sites FROM web_activities WHERE date BETWEEN ? AND ?
            AND site_name NOT IN (
                SELECT DISTINCT site_name  FROM web_activities WHERE date BETWEEN ? AND ?
            )
        """, (start_current_week, end_current_week, start_previous_week, end_previous_week))
        new_sites_result = cursor.fetchone()
        new_sites = new_sites_result["new_sites"] if new_sites_result and new_sites_result["new_sites"] is not None else 0
        
        # 3. TIEMPO TOTAL ESTA SEMANA vs SEMANA ANTERIOR
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM activities WHERE date BETWEEN ? AND ?
        """, (start_current_week, end_current_week))
        current_week_app_time_result = cursor.fetchone()
        current_week_app_time = current_week_app_time_result["total_hours"] if current_week_app_time_result and current_week_app_time_result["total_hours"] is not None else 0
        
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM web_activities WHERE date BETWEEN ? AND ?
        """, (start_current_week, end_current_week))
        current_week_web_time_result = cursor.fetchone()
        current_week_web_time = current_week_web_time_result["total_hours"] if current_week_web_time_result and current_week_web_time_result["total_hours"] is not None else 0
        
        current_week_total = current_week_app_time + current_week_web_time
        
        # Tiempo semana anterior
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM activities WHERE date BETWEEN ? AND ?
        """, (start_previous_week, end_previous_week))
        previous_week_app_time_result = cursor.fetchone()
        previous_week_app_time = previous_week_app_time_result["total_hours"] if previous_week_app_time_result and previous_week_app_time_result["total_hours"] is not None else 0
        
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM web_activities WHERE date BETWEEN ? AND ?
        """, (start_previous_week, end_previous_week))
        previous_week_web_time_result = cursor.fetchone()
        previous_week_web_time = previous_week_web_time_result["total_hours"] if previous_week_web_time_result and previous_week_web_time_result["total_hours"] is not None else 0
        
        previous_week_total = previous_week_app_time + previous_week_web_time
        
        # 4. PORCENTAJE DE CAMBIO
        time_change_percent = 0
        if previous_week_total > 0:
            time_change_percent = ((current_week_total - previous_week_total) / previous_week_total) * 100
        
        # 5. APPS ÚNICAS (total de apps diferentes esta semana)
        cursor.execute("""
            SELECT COUNT(DISTINCT app_name) as unique_apps FROM activities WHERE date BETWEEN ? AND ?
        """, (start_current_week, end_current_week))
        unique_apps_result = cursor.fetchone()
        unique_apps = unique_apps_result["unique_apps"] if unique_apps_result and unique_apps_result["unique_apps"] is not None else 0
        
        # 6. SITIOS ÚNICOS (total de sitios diferentes esta semana)
        cursor.execute("""
            SELECT COUNT(DISTINCT site_name) as unique_sites FROM web_activities WHERE date BETWEEN ? AND ?
        """, (start_current_week, end_current_week))
        unique_sites_result = cursor.fetchone()
        unique_sites = unique_sites_result["unique_sites"] if unique_sites_result and unique_sites_result["unique_sites"] is not None else 0
        
        session_data = await calculate_sessions_by_period(
            cursor,
            start_current_week,
            end_current_week,
            session_period
        )
        
        return {
            "time_total": {
                "hours": round(current_week_total, 1),
                "change_percent": round(time_change_percent, 1)
            },
            "unique_apps": {
                "count": unique_apps,
                "new_this_week": new_apps
            },
            "unique_sites": {
                "count": unique_sites, 
                "new_this_week": new_sites
            },
            "date_range": {
                "current_week": f"{start_current_week} to {end_current_week}",
                "previous_week": f"{start_previous_week} to {end_previous_week}"
            },
            "sessions": session_data
        }
        
    except Exception as e:
        return {"error": f"Error calculando cambios semanales: {e}"}
    finally:
        conn.close()


async def calculate_sessions_by_period(cursor, start_date, end_date, period="daily"):
    if period == "daily":
        cursor.execute("""
                       SELECT COUNT (*) as session_count
                       FROM(
                           SELECT DISTINCT date, app_name FROM activities
                           WHERE date BETWEEN ? AND ?
                           UNION
                           SELECT DISTINCT date, site_name FROM web_activities
                           WHERE date BETWEEN ? AND ?
                        )
                       """,(start_date, end_date, start_date, end_date))
    elif period == "weekly":
        cursor.execute("""
                       SELECT COUNT (*) as session_count
                       FROM(
                           SELECT DISTINCT strftime('%Y-%W', date) as week, app_name
                           FROM activities
                           WHERE date BETWEEN ? AND ?
                           UNION
                           SELECT DISTINCT strftime('%Y-%W', date) as week, site_name
                           FROM web_activities
                           WHERE date BETWEEN ? AND ?
                       )
                       """,(start_date, end_date, start_date, end_date))
    elif period == "monthly":
        cursor.execute("""
                       SELECT COUNT (*) as session_count
                       FROM(
                           SELECT DISTINCT strftime('%Y-%m', date) as month, app_name FROM activities
                           WHERE date BETWEEN ? AND ?
                           UNION
                           SELECT DISTINCT strftime('%Y-%m', date) as month, site_name
                           FROM web_activities
                           WHERE date BETWEEN ? AND ?  
                       )
                       """,(start_date, end_date, start_date, end_date))
    else:
        cursor.execute("""
                       SELECT COUNT (*) as session_count
                       FROM(
                           SELECT DISTINCT date, app_name FROM activities WHERE date BETWEEN ? AND ?
                           UNION
                           SELECT DISTINCT date, site_name FROM web_activities WHERE date BETWEEN ? AND ?
                       )
                       """,(start_date, end_date, start_date, end_date))
    session_data = cursor.fetchone()
    session_count = session_data["session_count"] if session_data else 0
    
    cursor.execute("""
                   SELECT COALESCE(SUM(duration), 0) as total_seconds FROM activities WHERE date BETWEEN ? AND ?
                   """, (start_date, end_date))
    app_seconds = cursor.fetchone()["total_seconds"]
    
    cursor.execute("""
                   SELECT COALESCE(SUM(duration), 0) as total_seconds FROM web_activities WHERE date BETWEEN ? AND ?
                   """, (start_date, end_date))
    web_seconds = cursor.fetchone()["total_seconds"]
    
    total_seconds = app_seconds + web_seconds
    
    avg_session_minutes = 0
    if session_count > 0:
        avg_session_minutes = (total_seconds / 60) / session_count
    return{
        "count": session_count,
        "avg_minutes":  round(avg_session_minutes, 1),
        "period": period
    }
    
    
    