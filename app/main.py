import asyncio
import sys

# FIX: Windows Selector Event Loop Policy for preventing freezes with SQLAlchemy/aiosqlite
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import Routers
from app.modules.auth.routes import router as auth_router
from app.modules.inventory.routes import router as inventory_router
from app.modules.sales.routes import router as sales_router
from app.modules.settings.routes import router as settings_router
from app.modules.catalog.routes import router as catalog_router
from app.modules.customers.routes import router as customers_router
from app.modules.marketing.routes import router as marketing_router

app = FastAPI(title="Enterprise Store Platform", version="2.0.0")

# Add Middleware
from app.middlewares.maintenance import MaintenanceMiddleware
app.add_middleware(MaintenanceMiddleware)

# Mount Static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(sales_router)
app.include_router(settings_router)
app.include_router(catalog_router)
app.include_router(customers_router)
app.include_router(marketing_router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

from fastapi import Request
templates = Jinja2Templates(directory="templates")

@app.get("/dashboard")
async def main_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Startup Event (Optional: Database Check)
from app.core.database import engine, Base, AsyncSessionLocal
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create tables if not exist (for dev convenience)
        # Note: In Modular Monolith, Base only knows about imported models.
        # Ideally, we should import all models here or allow migrations to handle it.
        # For this prototype to work immediately:
        from app.modules.inventory import models as inv_models
        from app.modules.sales import models as sales_models
        from app.modules.marketing import models as mkt_models
        from app.modules.settings import models as set_models
        from app.modules.auth import models as auth_models
        from app.modules.catalog import models as catalog_models
        from app.modules.customers import models as customers_models
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed default admin user if not exists
    from app.modules.auth.models import User, UserRole, SecuritySettings
    from app.core.security import get_password_hash
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.username == "admin")
        result = await session.execute(stmt)
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            print("Creating default admin user...")
            admin_user = User(
                username="admin",
                email="admin@store.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                full_name="System Administrator",
                is_active=True,
                token_version=1
            )
            admin_user.security_settings = SecuritySettings()
            session.add(admin_user)
            await session.commit()
            print("✅ Default admin user created successfully!")
        else:
            print("ℹ️  Admin user already exists, skipping seed.")

