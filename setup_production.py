"""
Production Database Setup Script
Run this after deploying to Render to initialize the database
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.modules.auth.models import User
from app.modules.auth.utils import hash_password
from datetime import datetime

async def setup_database():
    """Initialize database with tables and default admin user"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        return False
    
    # Convert postgres:// to postgresql:// if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Make it async
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create engine
        engine = create_async_engine(database_url, echo=True)
        
        # Create all tables
        print("📊 Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tables created successfully!")
        
        # Create default admin user
        print("👤 Creating default admin user...")
        
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Check if admin exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == "admin@store.com")
            )
            existing_admin = result.scalar_one_or_none()
            
            if not existing_admin:
                admin = User(
                    email="admin@store.com",
                    username="admin",
                    hashed_password=hash_password("admin123"),
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                session.add(admin)
                await session.commit()
                print("✅ Admin user created!")
                print(f"   📧 Email: admin@store.com")
                print(f"   🔑 Password: admin123")
            else:
                print("ℹ️  Admin user already exists")
            
            # Seed notification templates
            print("📧 Seeding notification templates...")
            from app.modules.settings.models import NotificationTemplate, NotificationEventType, NotificationChannel
            
            # Check if templates already exist
            from sqlalchemy import select
            result = await session.execute(select(NotificationTemplate))
            existing_templates = result.scalars().all()
            
            if not existing_templates:
                # Define default templates
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
        
        await engine.dispose()
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Visit your deployed app URL")
        print("   2. Login with: admin@store.com / admin123")
        print("   3. Change the password immediately!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 Production Database Setup")
    print("=" * 60)
    print()
    
    success = asyncio.run(setup_database())
    
    if not success:
        sys.exit(1)
    
    print("\n" + "=" * 60)
