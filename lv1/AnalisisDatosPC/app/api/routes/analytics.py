from fastapi import APIRouter, Depends, HTTPException
from app.database.connection import get_db_connection
from datetime import datetime, timedelta, date
from typing import Optional

router = APIRouter()

def calculate_period_dates(period: str):
    today = date.today()
    
    if period == "daily":
        start_date = today
        end_date = today
    elif period == "weekly":
        # Semana completa de lunes a domingo
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == "monthly":
        # Mes completo actual
        start_date = today.replace(day=1)
        # Último día del mes actual
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    else:  # "complete" o "total"
        # Desde el inicio de los registros hasta hoy
        start_date = date(2020, 1, 1)  # Fecha inicial por defecto
        end_date = today
    
    return start_date, end_date

def get_previous_period(start_date: date, end_date: date, period: str):
    days_diff = (end_date - start_date).days
    
    if period == "daily":
        prev_start = start_date - timedelta(days=1)
        prev_end = end_date - timedelta(days=1)
    elif period == "weekly":
        prev_start = start_date - timedelta(days=7)
        prev_end = end_date - timedelta(days=7)
    elif period == "monthly":
        # Mes anterior completo
        prev_start = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        prev_end = start_date - timedelta(days=1)
    else:  # complete
        # Para el período completo, comparar con el mismo período pero terminando ayer
        prev_end = start_date - timedelta(days=1)
        prev_start = start_date - timedelta(days=(days_diff + 1))
    
    return prev_start, prev_end

@router.get("/api/analytics")
async def get_analytics(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    period: str = "complete"  # Valor por defecto cambiado a weekly
):        
    """Análisis avanzados para la página de analytics"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la BD")
    
    try:
        # Si se proporcionan fechas específicas, usarlas; si no, calcular según período
        if start_date and end_date:
            start_date_obj = date.fromisoformat(start_date)
            end_date_obj = date.fromisoformat(end_date)
        else:
            start_date_obj, end_date_obj = calculate_period_dates(period)
            
        start_date_str = start_date_obj.isoformat()
        end_date_str = end_date_obj.isoformat()
        
        cursor = conn.cursor()
        
        # 1. TIEMPO TOTAL DE USO (en horas)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(duration), 0) / 3600.0 as total_hours
            FROM (
                SELECT duration FROM activities WHERE date BETWEEN ? AND ?
                UNION ALL
                SELECT duration FROM web_activities WHERE date BETWEEN ? AND ?
            )
        """, (start_date_str, end_date_str, start_date_str, end_date_str))
        total_hours = cursor.fetchone()[0] or 0
        
        # 2. DISTRIBUCIÓN POR CATEGORÍAS (con porcentajes)
        cursor.execute("""
            SELECT 
                COALESCE(c.category, 'Uncategorized') as category,
                COUNT(DISTINCT dcm.domain) as domain_count,
                SUM(COALESCE(wa.duration, 0)) as total_time
            FROM categories c
            LEFT JOIN domain_category_map dcm ON c.id = dcm.category_id
            LEFT JOIN web_activities wa ON dcm.domain = wa.site_name 
                AND wa.date BETWEEN ? AND ?
            GROUP BY c.id, c.category
            HAVING SUM(COALESCE(wa.duration, 0)) > 0
            ORDER BY total_time DESC;
        """, (start_date_str, end_date_str))
        categories_data = cursor.fetchall()
        
        # Calcular porcentajes solo con categorías que tienen tiempo
        total_category_time = sum(row[2] for row in categories_data)
        categories_with_percentages = []
        for category, domain_count, total_time in categories_data:
            percentage = (total_time / total_category_time * 100) if total_category_time > 0 else 0
            categories_with_percentages.append({
                "category": category,
                "domain_count": domain_count,
                "total_time": total_time,
                "percentage": round(percentage, 2),
                "hours": round(total_time / 3600, 2)
            })
        
        # 3. DISTRIBUCIÓN POR DÍA DE LA SEMANA
        cursor.execute("""
            SELECT 
                strftime('%w', date) as day_of_week,
                SUM(duration) / 3600.0 as hours
            FROM (
                SELECT date, duration FROM activities WHERE date BETWEEN ? AND ?
                UNION ALL
                SELECT date, duration FROM web_activities WHERE date BETWEEN ? AND ?
            )
            GROUP BY strftime('%w', date)
            ORDER BY strftime('%w', date)
        """, (start_date_str, end_date_str, start_date_str, end_date_str))
        daily_data = cursor.fetchall()
        
        # Mapear números de día a nombres
        day_names = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        daily_distribution = []
        for day_num, hours in daily_data:
            day_name = day_names[int(day_num)]
            daily_distribution.append({
                "day": day_name,
                "hours": round(hours, 2)
            })
        
        # 4. PATRONES DE SESIÓN
        # Sesiones totales y duración promedio
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                AVG(duration) as avg_duration_seconds
            FROM (
                SELECT duration FROM activities WHERE date BETWEEN ? AND ?
                UNION ALL
                SELECT duration FROM web_activities WHERE date BETWEEN ? AND ?
            )
        """, (start_date_str, end_date_str, start_date_str, end_date_str))
        session_stats = cursor.fetchone()
        total_sessions = session_stats[0] or 0
        avg_duration_minutes = round((session_stats[1] or 0) / 60, 1)
        
        # Distribución de duración de sesiones
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN duration <= 900 THEN '0-15 min'
                    WHEN duration <= 1800 THEN '15-30 min' 
                    WHEN duration <= 3600 THEN '30-60 min'
                    ELSE '60+ min'
                END as duration_range,
                COUNT(*) as session_count
            FROM (
                SELECT duration FROM activities WHERE date BETWEEN ? AND ?
                UNION ALL
                SELECT duration FROM web_activities WHERE date BETWEEN ? AND ?
            )
            GROUP BY duration_range
            ORDER BY 
                CASE duration_range
                    WHEN '0-15 min' THEN 1
                    WHEN '15-30 min' THEN 2
                    WHEN '30-60 min' THEN 3
                    ELSE 4
                END
        """, (start_date_str, end_date_str, start_date_str, end_date_str))
        session_distribution_data = cursor.fetchall()
        
        # Calcular porcentajes para distribución de sesiones
        session_distribution = []
        for duration_range, session_count in session_distribution_data:
            percentage = (session_count / total_sessions * 100) if total_sessions > 0 else 0
            session_distribution.append({
                "range": duration_range,
                "count": session_count,
                "percentage": round(percentage, 1)
            })
        
        # 5. TENDENCIAS (comparación con período anterior)
        prev_start, prev_end = get_previous_period(start_date_obj, end_date_obj, period)
        prev_start_str = prev_start.isoformat()
        prev_end_str = prev_end.isoformat()
        
        # Tiempo total período anterior
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) / 3600.0 as total_hours
            FROM (
                SELECT duration FROM activities WHERE date BETWEEN ? AND ?
                UNION ALL
                SELECT duration FROM web_activities WHERE date BETWEEN ? AND ?
            )
        """, (prev_start_str, prev_end_str, prev_start_str, prev_end_str))
        prev_total_hours = cursor.fetchone()[0] or 0
        
        # Calcular cambios porcentuales
        hours_change = 0
        if prev_total_hours > 0:
            hours_change = ((total_hours - prev_total_hours) / prev_total_hours) * 100
        
        # 6. ACTIVIDADES POR FECHA (para gráficos de tendencia)
        cursor.execute("""
            SELECT 
                date,
                SUM(duration) / 3600.0 as daily_hours
            FROM (
                SELECT date, duration FROM activities WHERE date BETWEEN ? AND ?
                UNION ALL
                SELECT date, duration FROM web_activities WHERE date BETWEEN ? AND ?
            )
            GROUP BY date
            ORDER BY date
        """, (start_date_str, end_date_str, start_date_str, end_date_str))
        daily_trends_data = cursor.fetchall()
        
        daily_trends = []
        for activity_date, daily_hours in daily_trends_data:
            daily_trends.append({
                "date": activity_date,
                "hours": round(daily_hours, 2)
            })
        
        return {
            "period": period,
            "period_date": {
                "start": start_date_str,
                "end": end_date_str,
                "previous_start": prev_start_str,
                "previous_end": prev_end_str
            },
            "total_hours": round(total_hours, 2),
            "categories": categories_with_percentages,
            "daily_distribution": daily_distribution,
            "sessions": {
                "total": total_sessions,
                "average_duration_minutes": avg_duration_minutes,
                "distribution": session_distribution
            },
            "trends": {
                "hours_change_percent": round(hours_change, 1),
                "previous_period_hours": round(prev_total_hours, 2),
                "daily_trends": daily_trends
            },
            "generatedAt": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en analytics: {str(e)}")
    finally:
        conn.close()