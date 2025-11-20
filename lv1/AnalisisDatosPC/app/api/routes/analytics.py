from fastapi import APIRouter, Depends
from app.database.connection import get_db_connection
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/api/analytics")
async def get_analytics(timeframe: str = "7d"):
    """Análisis avanzados para la página de analytics"""
    conn = get_db_connection()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}
    
    try:
        # Calcular fecha de inicio según timeframe
        today = datetime.now().date()
        
        if timeframe == "ayer":
            start_date = today - timedelta(days=1)
            end_date = today - timedelta(days=1)
        elif timeframe == "esta_semana":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif timeframe == "este_mes":
            start_date = today.replace(day=1)
            end_date = today
        elif timeframe == "completo":
            # Fecha muy antigua para obtener todos los datos
            start_date = today - timedelta(days=365*2)  # 2 años atrás
            end_date = today
        elif timeframe == "7d":
            start_date = today - timedelta(days=7)
            end_date = today
        elif timeframe == "30d":
            start_date = today - timedelta(days=30)
            end_date = today
        else:
            start_date = today - timedelta(days=7)
            end_date = today
            
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
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
                c.category,
                COUNT(DISTINCT dcm.domain) as domain_count,
                SUM(COALESCE(wa.duration, 0)) as total_time
            FROM categories c
            LEFT JOIN domain_category_map dcm ON c.id = dcm.category_id
            LEFT JOIN web_activities wa ON dcm.domain = wa.site_name 
                AND wa.date BETWEEN ? AND ?
            GROUP BY c.id, c.category
            ORDER BY total_time DESC;
        """, (start_date_str, end_date_str))
        categories_data = cursor.fetchall()
        
        # Calcular porcentajes
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
        # Calcular período anterior para comparación
        if timeframe == "ayer":
            prev_start = start_date - timedelta(days=1)
            prev_end = end_date - timedelta(days=1)
        elif timeframe == "esta_semana":
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date - timedelta(days=1)
        elif timeframe == "este_mes":
            # Mes anterior
            prev_start = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            prev_end = start_date - timedelta(days=1)
        else:
            # Para 7d, 30d, etc.
            period_days = (end_date - start_date).days
            prev_start = start_date - timedelta(days=period_days)
            prev_end = start_date - timedelta(days=1)
        
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
        
        return {
            "timeframe": timeframe,
            "period": {
                "start": start_date_str,
                "end": end_date_str
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
                "previous_period_hours": round(prev_total_hours, 2)
            },
            "generatedAt": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error en analytics: {str(e)}"}
    finally:
        conn.close()