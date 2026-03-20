from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager

from .database import engine, Base, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Remailder Data-IO Service",
    description="Serviciu asincron pentru gestionarea bazei de date",
    version="1.0.0",
    lifespan=lifespan
)

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