"""
Maintenance Mode Middleware
Checks if maintenance mode is enabled and blocks requests accordingly
"""
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select
from datetime import datetime
from app.core.database import get_db
from app.modules.settings.models import StoreSettings


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip check for static files and auth endpoints
        if request.url.path.startswith("/static") or request.url.path.startswith("/login"):
            return await call_next(request)
        
        # Check maintenance mode
        async for db in get_db():
            try:
                stmt = select(StoreSettings).limit(1)
                result = await db.execute(stmt)
                settings = result.scalar_one_or_none()
                
                if settings and settings.maintenance_mode_enabled:
                    maintenance_type = settings.maintenance_type or "fully_closed"
                    
                    # Check scheduled maintenance
                    if settings.maintenance_period_type == "scheduled":
                        now = datetime.now()
                        if settings.maintenance_start_at and settings.maintenance_end_at:
                            if not (settings.maintenance_start_at <= now <= settings.maintenance_end_at):
                                # Outside maintenance window, allow request
                                return await call_next(request)
                    
                    # Check daily schedule
                    if settings.maintenance_daily_schedule:
                        now = datetime.now()
                        day_name = now.strftime("%A").lower()  # monday, tuesday, etc.
                       
                        schedule = settings.maintenance_daily_schedule.get(day_name, {})
                        if schedule.get("enabled"):
                            start_time = schedule.get("start")
                            end_time = schedule.get("end")
                            
                            if start_time and end_time:
                                current_time = now.strftime("%H:%M")
                                if not (start_time <= current_time <= end_time):
                                    # Outside maintenance hours for today
                                    return await call_next(request)
                        else:
                            # No maintenance scheduled for today
                            return await call_next(request)
                    
                    # Maintenance is active
                    if maintenance_type == "fully_closed":
                        # Block all requests except API status checks
                        if request.url.path.startswith("/api"):
                            return JSONResponse(
                                status_code=503,
                                content={
                                    "error": "maintenance_mode",
                                    "message": settings.maintenance_message_ar or "الموقع قيد الصيانة",
                                    "message_en": settings.maintenance_message_en or "Site under maintenance"
                                }
                            )
                        
                        # Return HTML maintenance page
                        html_content = f"""
                        <!DOCTYPE html>
                        <html dir="rtl" lang="ar">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>{settings.maintenance_title_ar or 'صيانة'}</title>
                            <style>
                                body {{
                                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    min-height: 100vh;
                                    margin: 0;
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                }}
                                .container {{
                                    background: white;
                                    padding: 3rem;
                                    border-radius: 10px;
                                    box-shadow: 0 10px 50px rgba(0,0,0,0.2);
                                    text-align: center;
                                    max-width: 500px;
                                }}
                                h1 {{ color: #333; margin-bottom: 1rem; }}
                                p {{ color: #666; line-height: 1.6; }}
                                .icon {{ font-size: 4rem; margin-bottom: 1rem; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="icon">🔧</div>
                                <h1>{settings.maintenance_title_ar or 'الموقع قيد الصيانة'}</h1>
                                <p>{settings.maintenance_message_ar or 'نعتذر، الموقع قيد الصيانة حالياً. سنعود قريباً.'}</p>
                            </div>
                        </body>
                        </html>
                        """
                        return HTMLResponse(content=html_content, status_code=503)
                    
                    elif maintenance_type == "stop_orders":
                        # Block only order creation
                        if request.method == "POST" and "/api/orders" in request.url.path:
                            return JSONResponse(
                                status_code=503,
                                content={
                                    "error": "orders_disabled",
                                    "message": "إنشاء الطلبات معطل حالياً بسبب الصيانة"
                                }
                            )
                
            finally:
                await db.close()
        
        return await call_next(request)
