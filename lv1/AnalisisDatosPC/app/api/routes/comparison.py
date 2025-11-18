from fastapi import APIRouter, Depends
from app.database.connection import get_db_connection
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/api/comparison")  # Cambiamos el nombre para que sea más general
async def get_comparison(period: str = "weekly", session_period: str = "daily"):
    """Compara el período actual vs el período anterior"""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}
    
    try:
        cursor = conn.cursor()
        
        # Determinar rangos de fecha según el período
        date_ranges = await calculate_comparison_ranges(period)
        current_start = date_ranges["current_start"]
        current_end = date_ranges["current_end"]
        previous_start = date_ranges["previous_start"]
        previous_end = date_ranges["previous_end"]
        
        # 1. APPS NUEVAS EN EL PERÍODO ACTUAL
        cursor.execute("""
            SELECT COUNT(DISTINCT app_name) as new_apps FROM activities WHERE date BETWEEN ? AND ?
            AND app_name NOT IN (
                SELECT DISTINCT app_name FROM activities WHERE date BETWEEN ? AND ?
            )
        """, (current_start, current_end, previous_start, previous_end))
        new_apps_result = cursor.fetchone()
        new_apps = new_apps_result["new_apps"] if new_apps_result and new_apps_result["new_apps"] is not None else 0
        
        # 2. SITIOS NUEVOS EN EL PERÍODO ACTUAL
        cursor.execute("""
            SELECT COUNT(DISTINCT site_name) as new_sites FROM web_activities WHERE date BETWEEN ? AND ?
            AND site_name NOT IN (
                SELECT DISTINCT site_name FROM web_activities WHERE date BETWEEN ? AND ?
            )
        """, (current_start, current_end, previous_start, previous_end))
        new_sites_result = cursor.fetchone()
        new_sites = new_sites_result["new_sites"] if new_sites_result and new_sites_result["new_sites"] is not None else 0
        
        # 3. TIEMPO TOTAL PERÍODO ACTUAL vs ANTERIOR
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM activities WHERE date BETWEEN ? AND ?
        """, (current_start, current_end))
        current_app_time_result = cursor.fetchone()
        current_app_time = current_app_time_result["total_hours"] if current_app_time_result and current_app_time_result["total_hours"] is not None else 0
        
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM web_activities WHERE date BETWEEN ? AND ?
        """, (current_start, current_end))
        current_web_time_result = cursor.fetchone()
        current_web_time = current_web_time_result["total_hours"] if current_web_time_result and current_web_time_result["total_hours"] is not None else 0
        
        current_total = current_app_time + current_web_time
        
        # Tiempo período anterior
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM activities WHERE date BETWEEN ? AND ?
        """, (previous_start, previous_end))
        previous_app_time_result = cursor.fetchone()
        previous_app_time = previous_app_time_result["total_hours"] if previous_app_time_result and previous_app_time_result["total_hours"] is not None else 0
        
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours FROM web_activities WHERE date BETWEEN ? AND ?
        """, (previous_start, previous_end))
        previous_web_time_result = cursor.fetchone()
        previous_web_time = previous_web_time_result["total_hours"] if previous_web_time_result and previous_web_time_result["total_hours"] is not None else 0
        
        previous_total = previous_app_time + previous_web_time
        
        # 4. PORCENTAJE DE CAMBIO
        time_change_percent = 0
        if previous_total > 0:
            time_change_percent = ((current_total - previous_total) / previous_total) * 100
        elif current_total > 0:
            time_change_percent = 100  # Crecimiento desde cero
        
        # 5. APPS ÚNICAS (total de apps diferentes en el período actual)
        cursor.execute("""
            SELECT COUNT(DISTINCT app_name) as unique_apps FROM activities WHERE date BETWEEN ? AND ?
        """, (current_start, current_end))
        unique_apps_result = cursor.fetchone()
        unique_apps = unique_apps_result["unique_apps"] if unique_apps_result and unique_apps_result["unique_apps"] is not None else 0
        
        # 6. SITIOS ÚNICOS (total de sitios diferentes en el período actual)
        cursor.execute("""
            SELECT COUNT(DISTINCT site_name) as unique_sites FROM web_activities WHERE date BETWEEN ? AND ?
        """, (current_start, current_end))
        unique_sites_result = cursor.fetchone()
        unique_sites = unique_sites_result["unique_sites"] if unique_sites_result and unique_sites_result["unique_sites"] is not None else 0
        
        # 7. SESIONES (usando la función existente)
        session_data = await calculate_sessions_by_period(
            cursor,
            current_start,
            current_end,
            session_period
        )
        
        return {
            "time_total": {
                "hours": round(current_total, 1),
                "change_percent": round(time_change_percent, 1)
            },
            "unique_apps": {
                "count": unique_apps,
                "new_this_period": new_apps
            },
            "unique_sites": {
                "count": unique_sites, 
                "new_this_period": new_sites
            },
            "sessions": session_data,
            "period": period,
            "date_range": {
                "current": f"{current_start} to {current_end}",
                "previous": f"{previous_start} to {previous_end}"
            }
        }
        
    except Exception as e:
        return {"error": f"Error calculando comparación: {e}"}
    finally:
        conn.close()

async def calculate_comparison_ranges(period: str):
    """Calcula los rangos de fecha para comparación según el período"""
    today = datetime.now().date()
    
    if period == "daily":
        # Hoy vs Ayer
        current_start = today
        current_end = today
        previous_start = today - timedelta(days=1)
        previous_end = previous_start
    elif period == "weekly":
        # Esta semana vs Semana anterior
        current_start = today - timedelta(days=today.weekday())
        current_end = current_start + timedelta(days=6)
        previous_start = current_start - timedelta(days=7)
        previous_end = previous_start + timedelta(days=6)
    elif period == "monthly":
        # Este mes vs Mes anterior
        current_start = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        current_end = next_month - timedelta(days=next_month.day)
        
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end.replace(day=1)
    else:  # "weekly" por defecto
        current_start = today - timedelta(days=today.weekday())
        current_end = current_start + timedelta(days=6)
        previous_start = current_start - timedelta(days=7)
        previous_end = previous_start + timedelta(days=6)
    
    return {
        "current_start": current_start.isoformat(),
        "current_end": current_end.isoformat(),
        "previous_start": previous_start.isoformat(),
        "previous_end": previous_end.isoformat()
    }

# Mantenemos la misma función calculate_sessions_by_period que ya tienes
async def calculate_sessions_by_period(cursor, start_date, end_date, period="daily"):
    # ... (tu función existente igual)
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