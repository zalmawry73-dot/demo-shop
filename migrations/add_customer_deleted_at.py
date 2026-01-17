"""
Database Migration: Add deleted_at column to customers table for soft delete
Run this script to update the database schema
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.database import engine
from sqlalchemy import text

async def migrate():
    """Add deleted_at column to customers table"""
    async with engine.begin() as conn:
        try:
            # Check if column exists
            check_sql = """
            SELECT COUNT(*) as count 
            FROM pragma_table_info('customers') 
            WHERE name='deleted_at'
            """
            result = await conn.execute(text(check_sql))
            count = result.scalar()
            
            if count == 0:
                # Add the column
                alter_sql = """
                ALTER TABLE customers 
                ADD COLUMN deleted_at DATETIME NULL
                """
                await conn.execute(text(alter_sql))
                print("✅ تم إضافة عمود deleted_at بنجاح!")
            else:
                print("ℹ️ عمود deleted_at موجود بالفعل، لا حاجة للتحديث")
                
        except Exception as e:
            print(f"❌ خطأ في Migration: {e}")
            raise

if __name__ == "__main__":
    print("بدء Migration: إضافة عمود deleted_at...")
    asyncio.run(migrate())
    print("✅ Migration مكتمل!")
