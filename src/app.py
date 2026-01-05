from fastapi import FastAPI,HTTPException,File,UploadFile,Form,Depends
from src.db import create_db_and_tables,get_session,Post
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from src.images import imagekit
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"Hello": "World"}



@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(""),
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
async def get_feed(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]
    
    posts_data = []
    for post in posts:
        posts_data.append({
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        })
    return posts_data

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, session: AsyncSession = Depends(get_session)):
    try:
        post_id = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        await session.delete(post)
        await session.commit()
        return {"detail": "Post deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")