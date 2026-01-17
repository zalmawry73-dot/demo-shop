from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Database URL
# Note: For production, this should be an environment variable.
# Using SQLite async for demonstration, but scalable to Postgres.
DATABASE_URL = "sqlite+aiosqlite:///./store_v2.db" 
# For Postgres: "postgresql+asyncpg://user:password@localhost/dbname"

from sqlalchemy.pool import NullPool

engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
