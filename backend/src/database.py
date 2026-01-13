from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import get_settings

settings = get_settings()

# Use async_database_url which converts postgres:// to postgresql+asyncpg://
database_url = settings.async_database_url

# Debug: show which database we're connecting to
print(f"DATABASE CONFIG: Using database URL: {database_url[:50]}..." if len(database_url) > 50 else f"DATABASE CONFIG: Using database URL: {database_url}")

# Adjust pool settings based on database type
is_sqlite = database_url.startswith("sqlite")

engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    # SQLite doesn't support connection pooling the same way
    **({"pool_recycle": 300, "pool_size": 5, "max_overflow": 10} if not is_sqlite else {})
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database and create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized - all tables created/verified")
