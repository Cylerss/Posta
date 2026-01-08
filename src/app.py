from fastapi import FastAPI,HTTPException,File,UploadFile,Form,Depends
from .db.db import create_db_and_tables,get_session,Post,User
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from .images import imagekit
import uuid
from .auth.users import current_active_user,auth_backend,fastapi_users
from .models.schemas import UserRead,PostResponse,PostCreate,UserCreate,UserUpdate
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead,UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])   
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
                                                            
@app.get("/")
async def read_root():
    return {"Hello": "World"}



@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(""),
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_session)
):
    file_content = await file.read()
    upload_response = imagekit.files.upload(
        file=file_content,
        file_name=file.filename,
        folder="/fastapi_uploads/"
    )
    if not upload_response.url:
        raise HTTPException(status_code=500, detail="Upload failed")
    file_url = upload_response.url
    if file.content_type.startswith("image/"):
        file_type = "photo"
    elif file.content_type.startswith("video/"):
        file_type = "video"
    else:
        file_type = "file"
    post = Post(
        user_id=user.id,
        caption=caption,
        url=file_url,
        file_type=file_type,
        file_name=file.filename
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_session),user: User = Depends(current_active_user)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]
    
    
    posts_data = []
    for post in posts:
        posts_data.append({
            "id": str(post.id),
            "user_id": str(post.user_id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
            "is_owner": post.user_id == user.id ,
            "email": user.email
        })
    return posts_data

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, session: AsyncSession = Depends(get_session),user: User = Depends(current_active_user)):
    try:
        post_id = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        await session.delete(post)
        await session.commit()
        return {"detail": "Post deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")