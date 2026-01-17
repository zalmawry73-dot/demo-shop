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
