import asyncio

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from contextlib import asynccontextmanager
from .worker import start_rabbitmq_consumer
from .models import User, EmailLog
from .database import engine, Base, get_db
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    worker_task = asyncio.create_task(start_rabbitmq_consumer())

    yield

    worker_task.cancel()

app = FastAPI(
    title="Remailder Data-IO Service",
    description="Serviciu asincron pentru gestionarea bazei de date",
    version="1.0.0",
    lifespan=lifespan
)

# --------- API Endpoints ---------


# --------- Health Check Endpoints ---------

@app.get("/health")
async def health():
    return {"status": "ok", "python_version": "3.12"}

@app.get("/health/db")
async def db_check(db: AsyncSession = Depends(get_db)):
    """Verifică dacă baza de date este conectată și funcțională."""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "connection_string_host": engine.url.host
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Database connection failed: {str(e)}"
        )
    
# --------- Endpoints for authentication ---------

class UserCreate(BaseModel):
    """Schema for creating a new user with a pre-hashed password."""
    email: str
    password_hash: str

class UserResponse(BaseModel):
    """Schema for returning user data, excluding sensitive fields by default."""
    id: int
    email: str

    class Config:
        from_attributes = True

@app.post("/users", response_model=UserResponse)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user record in the database.
    This method is used during the Registration process.
    """
    # Check if email already exists
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_in.email, 
        password_hash=user_in.password_hash
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.get("/users/{email}")
async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve user details including password_hash for authentication purposes.
    This method is used by the Auth-Service during the Login process.
    """
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "password_hash": user.password_hash
    }

@app.delete("/users/{email}")
async def delete_user(email: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a user by email. This will also cascade delete all associated email logs.
    """
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    
    return {"detail": "User deleted successfully"}

# --------- Endpoints for email logs management ---------

@app.get("/logs/{user_id}")
async def get_user_logs(user_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve all email logs for a specific user ID."""
    query = select(EmailLog).where(EmailLog.id_user == user_id)
    result = await db.execute(query)
    return result.scalars().all()