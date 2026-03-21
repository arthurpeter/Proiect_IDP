from fastapi import FastAPI
import httpx
import aio_pika
import os

app = FastAPI(title="Remailder Main Manager")

IO_SERVICE_URL = "http://io-service:8000"

@app.get("/")
async def root():
    return {"message": "Main Manager is running"}

@app.get("/test-io")
async def test_io():
    """Test if Main-Service can talk to IO-Service inside K8s."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{IO_SERVICE_URL}/health")
    return response.json()