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
        if timeframe == "7d":
            days = 7
        elif timeframe == "30d":
            days = 30
        else:
            days = 7
            
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        end_date = datetime.now().date().isoformat()
        
        cursor = conn.cursor()
        
        # Tendencia de uso de aplicaciones (horas por día)
        cursor.execute("""
            SELECT 
                date,
                SUM(duration) / 3600.0 as hours
            FROM activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))
        app_usage_trend = [dict(row) for row in cursor.fetchall()]
        
        # Tendencia de uso web (horas por día)
        cursor.execute("""
            SELECT 
                date,
                SUM(duration) / 3600.0 as hours
            FROM web_activities 
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))
        web_usage_trend = [dict(row) for row in cursor.fetchall()]
        
        return {
            "appUsageTrend": app_usage_trend,
            "webUsageTrend": web_usage_trend,
            "timeframe": timeframe,
            "generatedAt": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Error en analytics: {e}"}
    finally:
        conn.close()
   