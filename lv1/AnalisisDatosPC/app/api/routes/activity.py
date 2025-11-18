from fastapi import APIRouter, Depends, Request
from app.database.activity_repo import safe_page_navegator, view_domain, save_domain_category
from app.api.IA.iaohttp import classify_domain
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

        category_id = view_domain(domain)
        if category_id : 
            #Revisar si existe o no el dominio categorizado, si esta bien guardar solo la consulta de navegador
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
        else: 
            #si no existe llamar a la ia para que nos de un id de categoria
            print("Categoria no encontrada")
            category_id = await classify_domain(domain)
            print(f"Categoria asignada por ia ID {category_id}")
            save_domain_category(domain,category_id)
        

        print(f"Página guardada correctamente: {domain}")
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error procesando actividad: {e}")
        return {"status": "error", "message": str(e)}
    
