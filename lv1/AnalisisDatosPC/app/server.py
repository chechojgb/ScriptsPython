from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import init_db
from app.database.activity_repo import safe_page_navegator
from app.config import Config
from contextlib import asynccontextmanager
from datetime import datetime, date

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

# Permitir peticiones desde el navegador/extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)