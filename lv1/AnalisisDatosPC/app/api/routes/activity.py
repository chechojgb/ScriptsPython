from fastapi import APIRouter, Depends, Request
from app.database.activity_repo import safe_page_navegator
from app.database.connection import get_db_connection
from datetime import datetime, timedelta
router = APIRouter()

@router.post("/activity")
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
        
        print(f"Guardando: {domain} - {duration}s")
        print(f"Horas: {start_time_str} a {end_time_str}")
        print(f"Fecha: {date_today}")

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

        print(f"Página guardada correctamente: {domain}")
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error procesando actividad: {e}")
        return {"status": "error", "message": str(e)}
