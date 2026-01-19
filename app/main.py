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
        
        # Seed notification templates if not exist
        from app.modules.settings.models import NotificationTemplate, NotificationEventType, NotificationChannel
        
        stmt = select(NotificationTemplate)
        result = await session.execute(stmt)
        existing_templates = result.scalars().all()
        
        if not existing_templates:
            print("📧 Seeding notification templates...")
            templates = [
                # SMS Templates
                {
                    "event_type": NotificationEventType.ORDER_CREATED,
                    "channel": NotificationChannel.SMS,
                    "message_template_ar": "مرحباً {customer_name}، تم استلام طلبك #{order_id} بنجاح. شكراً لثقتك بنا!",
                    "message_template_en": "Hello {customer_name}, your order #{order_id} has been received successfully. Thank you!"
                },
                {
                    "event_type": NotificationEventType.ORDER_PROCESSING,
                    "channel": NotificationChannel.SMS,
                    "message_template_ar": "طلبك #{order_id} قيد التجهيز الآن. سنقوم بإشعارك عند شحنه.",
                    "message_template_en": "Your order #{order_id} is now being processed. We'll notify you when it ships."
                },
                {
                    "event_type": NotificationEventType.ORDER_READY,
                    "channel": NotificationChannel.SMS,
                    "message_template_ar": "طلبك #{order_id} جاهز للشحن!",
                    "message_template_en": "Your order #{order_id} is ready for shipping!"
                },
                {
                    "event_type": NotificationEventType.ORDER_SHIPPED,
                    "channel": NotificationChannel.SMS,
                    "message_template_ar": "تم شحن طلبك #{order_id}. سيصلك قريباً!",
                    "message_template_en": "Your order #{order_id} has been shipped. It will arrive soon!"
                },
                {
                    "event_type": NotificationEventType.ORDER_COMPLETED,
                    "channel": NotificationChannel.SMS,
                    "message_template_ar": "تم تسليم طلبك #{order_id} بنجاح. نتمنى أن تكون راضياً عن تجربتك!",
                    "message_template_en": "Your order #{order_id} has been delivered successfully. We hope you enjoyed your experience!"
                },
                {
                    "event_type": NotificationEventType.ORDER_CANCELLED,
                    "channel": NotificationChannel.SMS,
                    "message_template_ar": "تم إلغاء طلبك #{order_id}. إذا كان لديك أي استفسار، يرجى التواصل معنا.",
                    "message_template_en": "Your order #{order_id} has been cancelled. If you have any questions, please contact us."
                },
                
                # WhatsApp Templates
                {
                    "event_type": NotificationEventType.ORDER_CREATED,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_template_ar": "🎉 مرحباً {customer_name}!\n\nتم استلام طلبك #{order_id} بنجاح.\nسنقوم بمعالجته في أقرب وقت.\n\nشكراً لاختيارك {store_name}",
                    "message_template_en": "🎉 Hello {customer_name}!\n\nYour order #{order_id} has been received.\nWe'll process it shortly.\n\nThank you for choosing {store_name}"
                },
                {
                    "event_type": NotificationEventType.ORDER_PROCESSING,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_template_ar": "⏳ طلبك #{order_id} قيد التجهيز\n\nنحن نعمل على تجهيز طلبك الآن.\nسنشعرك عندما يكون جاهزاً للشحن!",
                    "message_template_en": "⏳ Your order #{order_id} is being processed\n\nWe're working on preparing your order.\nWe'll notify you when it's ready to ship!"
                },
                {
                    "event_type": NotificationEventType.ORDER_READY,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_template_ar": "✅ طلبك #{order_id} جاهز!\n\nطلبك جاهز الآن للشحن.\nسيتم إرساله قريباً.",
                    "message_template_en": "✅ Your order #{order_id} is ready!\n\nYour order is now ready for shipping.\nIt will be sent soon."
                },
                {
                    "event_type": NotificationEventType.ORDER_SHIPPED,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_template_ar": "🚚 تم شحن طلبك #{order_id}!\n\nطلبك في الطريق إليك.\nسيصلك خلال الأيام القادمة.",
                    "message_template_en": "🚚 Your order #{order_id} has shipped!\n\nYour order is on its way.\nIt will arrive in the coming days."
                },
                {
                    "event_type": NotificationEventType.ORDER_COMPLETED,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_template_ar": "🎁 تم تسليم طلبك #{order_id}\n\nنأمل أن تكون راضياً عن طلبك!\nشكراً لثقتك بنا.",
                    "message_template_en": "🎁 Your order #{order_id} delivered\n\nWe hope you're satisfied with your order!\nThank you for trusting us."
                },
                {
                    "event_type": NotificationEventType.ORDER_CANCELLED,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_template_ar": "❌ تم إلغاء طلبك #{order_id}\n\nإذا كان لديك أي استفسار، لا تتردد في التواصل معنا.",
                    "message_template_en": "❌ Your order #{order_id} cancelled\n\nIf you have any questions, don't hesitate to contact us."
                },
                
                # Email Templates (disabled by default)
                {
                    "event_type": NotificationEventType.ORDER_CREATED,
                    "channel": NotificationChannel.EMAIL,
                    "is_enabled": False,
                    "message_template_ar": "مرحباً {customer_name}، تم استلام طلبك #{order_id}",
                    "message_template_en": "Hello {customer_name}, your order #{order_id} received"
                },
                {
                    "event_type": NotificationEventType.ORDER_PROCESSING,
                    "channel": NotificationChannel.EMAIL,
                    "is_enabled": False,
                    "message_template_ar": "طلبك #{order_id} قيد التجهيز",
                    "message_template_en": "Your order #{order_id} is processing"
                },
                {
                    "event_type": NotificationEventType.ORDER_SHIPPED,
                    "channel": NotificationChannel.EMAIL,
                    "is_enabled": False,
                    "message_template_ar": "تم شحن طلبك #{order_id}",
                    "message_template_en": "Your order #{order_id} shipped"
                },
                {
                    "event_type": NotificationEventType.ORDER_COMPLETED,
                    "channel": NotificationChannel.EMAIL,
                    "is_enabled": False,
                    "message_template_ar": "تم تسليم طلبك #{order_id}",
                    "message_template_en": "Your order #{order_id} delivered"
                },
                {
                    "event_type": NotificationEventType.ORDER_CANCELLED,
                    "channel": NotificationChannel.EMAIL,
                    "is_enabled": False,
                    "message_template_ar": "تم إلغاء طلبك #{order_id}",
                    "message_template_en": "Your order #{order_id} cancelled"
                },
            ]
            
            # Create templates
            for template_data in templates:
                template = NotificationTemplate(**template_data)
                session.add(template)
            
            await session.commit()
            print(f"✅ Created {len(templates)} notification templates!")
        else:
            print(f"ℹ️  Notification templates already exist ({len(existing_templates)} templates)")


