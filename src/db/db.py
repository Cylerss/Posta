from collections.abc import AsyncGenerator
from datetime import timezone,datetime
import uuid
from dotenv import load_dotenv
from sqlalchemy import Column, String, Text,DateTime,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
import os
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi import Depends


load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID,Base):
    posts=relationship("Post",back_populates="user")


DATABASE_URL=os.getenv("POSTGES_URL")

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id=Column(UUID(as_uuid=True), ForeignKey("user.id"),nullable=False)
    user=relationship("User",back_populates="posts")
    caption=Column(Text)
    url=Column(String, nullable=False)
    file_type=Column(String, nullable=False)
    file_name=Column(String, nullable=False)
    created_at=Column(DateTime, nullable=False,default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={'ssl': 'require'})
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
        
        
async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)
    

    
