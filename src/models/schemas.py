from pydantic import BaseModel
from fastapi_users import schemas
import uuid

class PostCreate(BaseModel):
    title: str
    caption: str | None = None
  
class PostResponse(BaseModel):
    title: str
    caption: str | None = None
  
class UserRead(schemas.BaseUser[uuid.UUID]):
    pass
  
class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

