from collections.abc import AsyncGenerator
import datetime
from datetime import timezone
import uuid

from sqlalchemy import Column, String, Text,DateTime,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

DATABASE_URL="postgresql+asyncpg://neondb_owner:npg_xhd2eLPp4MEX@ep-royal-night-adm7va76-pooler.c-2.us-east-1.aws.neon.tech/Testdb"

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption=Column(Text)
    url=Column(String, nullable=False)
    file_type=Column(String, nullable=False)
    file_name=Column(String, nullable=False)
    created_at=Column(DateTime, nullable=False,default=lambda: datetime.datetime.now(timezone.utc).replace(tzinfo=None))

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={'ssl': 'require'})
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session