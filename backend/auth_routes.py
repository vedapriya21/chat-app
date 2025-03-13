from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.model import User 
from backend.auth import hash_password, verify_password, create_access_token 

router = APIRouter()

@router.post("/signup")
async def signup(username: str, password: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.username == username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(username=username, password_hash=hash_password(password))  
    db.add(user)
    await db.commit()
    
    return {"message": "User created successfully"}

@router.post("/login")
async def login(username: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user or not verify_password(password, user.password_hash): 
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(data={"sub": username})
    return {"access_token": token, "token_type": "bearer"}
