from fastapi import APIRouter, HTTPException
from app.database.connection import get_db_connection
from datetime import datetime, timedelta
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/reports_format")
async def get_reports(
    start_date: str = None, 
    end_date: str = None,
    period: str = "complete"
):
    """
    Reportes históricos flexibles por período
    
    Retorna:
    - Tiempo por aplicación (top 10)
    - Tiempo por sitio web (top 10) 
    - Metadatos del reporte
    """
    # Validar parámetros
    if period not in ["daily", "weekly", "monthly", "complete"]:
        raise HTTPException(status_code=400, detail="Período no válido. Use: daily, weekly, monthly, complete")
    
    # Validar formato de fechas si se proporcionan
    if start_date:
        await validate_date_format(start_date)
    if end_date:
        await validate_date_format(end_date)
    
    conn = get_db_connection()
    if not conn:
        logger.error("No se pudo conectar a la base de datos")
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    
    try:
        cursor = conn.cursor()
        
        # Determinar fechas según el período
        date_range = await calculate_date_range(period, start_date, end_date)
        start_date_str = date_range["start_date"]
        end_date_str = date_range["end_date"]
        
        logger.info(f"Generando reporte para {start_date_str} - {end_date_str}, período: {period}")
        
        # Tiempo por aplicación - CON manejo de NULL y formato consistente
        cursor.execute("""
            SELECT 
                COALESCE(app_name, 'Sin nombre') as name,
                ROUND(COALESCE(SUM(duration), 0) / 3600.0, 2) as hours,
                COUNT(*) as sessions
            FROM activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY app_name 
            ORDER BY hours DESC
            LIMIT 10
        """, (start_date_str, end_date_str))
        apps_time = [dict(row) for row in cursor.fetchall()]
        
        # Tiempo por sitio web - CON manejo de NULL y formato consistente
        cursor.execute("""
            SELECT 
                COALESCE(site_name, 'Sin nombre') as name,
                ROUND(COALESCE(SUM(duration), 0) / 3600.0, 2) as hours,
                COUNT(*) as visits
            FROM web_activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY site_name 
            ORDER BY hours DESC
            LIMIT 10
        """, (start_date_str, end_date_str))
        sites_time = [dict(row) for row in cursor.fetchall()]

        # Estadísticas generales
        cursor.execute("""
            SELECT 
                ROUND(COALESCE(SUM(total_hours), 0), 2) as total_hours,
                COUNT(DISTINCT name) as unique_items
            FROM (
                SELECT 
                    SUM(duration) / 3600.0 as total_hours,
                    app_name as name,
                    'app' as type
                FROM activities 
                WHERE date BETWEEN ? AND ?
                GROUP BY app_name
                
                UNION ALL
                
                SELECT 
                    SUM(duration) / 3600.0 as total_hours,
                    site_name as name,
                    'site' as type
                FROM web_activities 
                WHERE date BETWEEN ? AND ?
                GROUP BY site_name
            ) combined
        """, (start_date_str, end_date_str, start_date_str, end_date_str))
        combined_stats = dict(cursor.fetchone() or {})
        
        # Calcular porcentajes para apps
        total_apps_hours = sum(app['hours'] for app in apps_time)
        for app in apps_time:
            app['percentage'] = round((app['hours'] / total_apps_hours * 100) if total_apps_hours > 0 else 0, 1)
        
        # Calcular porcentajes para sitios
        total_sites_hours = sum(site['hours'] for site in sites_time)
        for site in sites_time:
            site['percentage'] = round((site['hours'] / total_sites_hours * 100) if total_sites_hours > 0 else 0, 1)

        return {
            "success": True,
            "data": {
                "appsTime": apps_time,
                "sitesTime": sites_time,
                "summary": {
                    "totalHours": combined_stats.get('total_hours'),
                    "uniqueApps": combined_stats.get('unique_items', 0),
                    "totalWebsites": len(sites_time),
                    "period": period
                }
            },
            "metadata": {
                "dateRange": {
                    "start": start_date_str,
                    "end": end_date_str
                },
                "generatedAt": datetime.now().isoformat(),
                "period": period
            }
        }
        
    except Exception as e:
        logger.error(f"Error generando reportes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    finally:
        if conn:
            conn.close()

async def calculate_date_range(period: str, start_date: str = None, end_date: str = None):
    """Calcula el rango de fechas según el período con validación mejorada"""
    today = datetime.now().date()
    
    # Si se proporcionan ambas fechas, usarlas
    if start_date and end_date and start_date.strip() and end_date.strip():
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if start_dt > end_dt:
                raise ValueError("La fecha de inicio no puede ser mayor que la fecha de fin")
                
            return {
                "start_date": start_date,
                "end_date": end_date
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {str(e)}")
    
    # Calcular según período
    if period == "daily":
        start = today
        end = today
    elif period == "weekly":
        start = today - timedelta(days=today.weekday())  # Lunes de esta semana
        end = start + timedelta(days=6)  # Domingo
    elif period == "monthly":
        start = today.replace(day=1)  # Primer día del mes
        # Último día del mes
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    else:  # "complete" - todo el historial
        start = "2020-01-01"  # O podrías obtener la fecha más antigua de la BD
        end = today
    
    return {
        "start_date": start.isoformat() if hasattr(start, 'isoformat') else start,
        "end_date": end.isoformat() if hasattr(end, 'isoformat') else end
    }

async def validate_date_format(date_str: str):
    """Valida que la fecha tenga el formato correcto"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {date_str}. Use YYYY-MM-DD")