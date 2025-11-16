from app.api.routes import activity, status, real_time, reports, weekly_changes, analytics

def register_routes(app):
    """Registrar todos los routers en la app"""
    app.include_router(activity.router)
    app.include_router(status.router)
    app.include_router(real_time.router)
    app.include_router(reports.router)
    app.include_router(weekly_changes.router)
    app.include_router(analytics.router)