from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - create tables if they don't exist"""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.models import user, chore, carbon_intensity, league, task, monthly_summary, notification
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)