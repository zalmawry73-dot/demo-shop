
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.database import DATABASE_URL, Base
from app.core.security import get_password_hash

# Import all models to ensure Base.metadata is populated
from app.modules.inventory import models as inv
from app.modules.sales import models as sales
from app.modules.customers import models as cust
from app.modules.marketing import models as mkt
from app.modules.settings import models as sett
from app.modules.auth import models as auth
from app.modules.customers import models as cust

import os

async def reset_database():
    # Force delete the database file to ensure a clean slate
    db_file = "store_v2.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"Deleted existing {db_file}")
        except Exception as e:
            print(f"Warning: Could not delete {db_file}: {e}")

    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # Handle SQLite sequence if needed
        try:
            await conn.execute(text("DELETE FROM sqlite_sequence"))
        except:
            pass

        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        print("Schema Updated & Tables Cleaned.")
        
        # Seed Admin
        print("Seeding Admin User...")
        # Since tables are recreated, we insert raw or via ORM. 
        # Raw is faster/safer in this script without session overhead if simple.
        # But we need hash.
        
        admin_pass = get_password_hash("admin123")
        # Note: timestamps are handled by server_default in DB usually, but some drivers need strict generic handling
        
        try:
            # Create Admin User
            await conn.execute(text(f"""
                INSERT INTO users (username, email, password_hash, role, is_active, full_name, token_version) 
                VALUES ('admin', 'admin@store.com', '{admin_pass}', 'ADMIN', 1, 'System Administrator', 1)
            """))
            
            # Get Admin ID (SQLite specific likely 1, but safer to subquery or just know it's first)
            # Actually, we can assume it's ID 1 if we just reset.
            
            # Create Security Settings for Admin
            await conn.execute(text("""
                INSERT INTO security_settings (user_id, two_factor_enabled, export_password_protection, otp_method, session_policy, created_at, updated_at)
                VALUES ((SELECT id FROM users WHERE username='admin'), 0, 0, 'SMS', 'NORMAL', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))

        except Exception as e:
            print(f"User exists or Creation Logic Error... ({e})")
            # If user exists, try to ensure security settings exist
            try:
                await conn.execute(text("""
                    INSERT INTO security_settings (user_id, two_factor_enabled, export_password_protection, otp_method, session_policy, created_at, updated_at)
                    VALUES ((SELECT id FROM users WHERE username='admin'), 0, 0, 'SMS', 'NORMAL', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """))
            except:
                pass # Already exists
        
        print("Seeding Main Warehouse...")
        try:
            await conn.execute(text("""
                INSERT INTO warehouses (name, location, branch_type, priority_index, is_active)
                VALUES ('Main Store', 'Riyadh', 'WAREHOUSE', 0, 1)
            """))
        except:
             print("Skipping Warehouse Seed: Likely exists.")

    print("Database Reset Complete. Ready for Production.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_database())
