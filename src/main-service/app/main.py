import json
import asyncio
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, Header, HTTPException
import aio_pika

from .config import settings
from .worker import email_consumer

# --- FastAPI Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(email_consumer())
    yield
    worker_task.cancel()

app = FastAPI(title="Remailder Main Manager", lifespan=lifespan)

# --- Routes ---

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    scheduled_at: datetime

@app.post("/schedule")
async def schedule_email(
    payload: EmailRequest,
    x_user_id: int = Header(..., alias="X-User-Id", description="ID of the user")
):
    now = datetime.now(timezone.utc)
    
    scheduled = payload.scheduled_at
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
        
    delay_ms = int((scheduled - now).total_seconds() * 1000)
    
    if delay_ms < 0:
        delay_ms = 0 

    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()

            create_msg = {
                "action": "create",
                "user_id": x_user_id,
                "to": payload.to,
                "subject": payload.subject,
                "scheduled_at": payload.scheduled_at.isoformat()
            }
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(create_msg).encode()),
                routing_key="db_tasks"
            )

            delayed_exchange = await channel.declare_exchange(
                name="delayed_exchange",
                type="x-delayed-message",
                arguments={"x-delayed-type": "direct"},
                durable=True
            )

            queue = await channel.declare_queue("send_emails", durable=True)
            
            await queue.bind(delayed_exchange, routing_key="send_emails")

            email_job_msg = {
                "user_id": x_user_id,
                "to": payload.to,
                "subject": payload.subject,
                "body": payload.body
            }

            await delayed_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(email_job_msg).encode(),
                    headers={"x-delay": delay_ms} 
                ),
                routing_key="send_emails"
            )

        return {
            "message": "Email scheduled successfully",
            "delay_ms": delay_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))