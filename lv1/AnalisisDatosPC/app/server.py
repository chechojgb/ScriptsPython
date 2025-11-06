# server.py (actualizado)
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import init_db
from app.database.activity_repo import safe_page_navegator
from app.config import Config
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta
import sqlite3
import os
from pathlib import Path

# Lifespan manager primero
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("TrackerK API iniciada correctamente")
    yield
    # Shutdown
    print("Cerrando TrackerK API")

# Crear la app UNA sola vez con lifespan
app = FastAPI(title="TrackerK API", lifespan=lifespan)

# Permitir peticiones desde el navegador/extension Y del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Conectar a la BD SQLite"""
    try:
        # Tu BD ya está en AppData gracias a tu Config
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error conectando a BD: {e}")
        return None

# ==================== ENDPOINTS PARA LA EXTENSIÓN (EXISTENTES) ====================

@app.post("/activity")
async def receive_activity(request: Request):
    try:
        data = await request.json()
        print("📩 Recibido:", data)
        
        # Extraer datos
        domain = data.get("domain")
        url = data.get("url")
        title = data.get("title")
        startTime = data.get("startTime")
        endTime = data.get("endTime")
        browser = data.get("browser")
        duration = data.get("duration")
        
        # Convertir timestamps UTC a hora local
        start_dt_utc = datetime.fromisoformat(startTime.replace('Z', '+00:00'))
        end_dt_utc = datetime.fromisoformat(endTime.replace('Z', '+00:00'))
        
        # Convertir a hora local
        start_dt_local = start_dt_utc.astimezone()
        end_dt_local = end_dt_utc.astimezone()
        
        # Preparar datos para la BD
        date_today = start_dt_local.date()
        status = "closed"
        start_time_str = start_dt_local.strftime("%H:%M:%S")
        end_time_str = end_dt_local.strftime("%H:%M:%S")
        
        print(f"💾 Guardando: {domain} - {duration}s")
        print(f"🕒 Horas: {start_time_str} a {end_time_str}")
        print(f"📅 Fecha: {date_today}")

        # Usar función específica para datos de extensión
        safe_page_navegator(
            browser,           # browser
            domain,            # site_name
            start_time_str,    # start_time (string)
            end_time_str,      # end_time (string)
            duration,          # duration
            date_today,        # date
            status             # status
        )

        print(f"✅ Página guardada correctamente: {domain}")
        return {"status": "ok"}
        
    except Exception as e:
        print(f"❌ Error procesando actividad: {e}")
        return {"status": "error", "message": str(e)}

# ==================== NUEVOS ENDPOINTS PARA EL FRONTEND REACT ====================

# En tu server.py - REEMPLAZAR los endpoints existentes con estos:

@app.get("/api/status")
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

@app.get("/api/real-time")
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

@app.get("/api/reports")
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

@app.get("/api/analytics")
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
        
if __name__ == "__main__":
    import uvicorn
    # Cambiar a puerto 8000 para el frontend (estándar)
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")