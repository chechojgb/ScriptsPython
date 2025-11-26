from app.api.routes import activity, comparison, status, real_time, reports, analytics , reports_format

def register_routes(app):
    """Registrar todos los routers en la app"""
    app.include_router(activity.router)
    app.include_router(status.router)
    app.include_router(real_time.router)
    app.include_router(reports.router)
    app.include_router(comparison.router)
    app.include_router(analytics.router)
    app.include_router(reports_format.router)