import asyncio
import json
import aio_pika
from .database import AsyncSessionLocal
from .models import EmailLog
from .config import settings
from datetime import datetime

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = json.loads(message.body)
        print(f"Recieved message: {body}")

        scheduled_str = body.get("scheduled_at")
        scheduled_dt = None
        if scheduled_str:
            scheduled_dt = datetime.fromisoformat(scheduled_str)
        
        async with AsyncSessionLocal() as session:
            new_log = EmailLog(
                id_user=body.get("user_id"),
                recipient=body.get("to"),
                subject=body.get("subject"),
                status="pending",
                scheduled_at=scheduled_dt
            )
            session.add(new_log)
            await session.commit()
            print(f"Saved log for {body.get('to')}")

async def start_rabbitmq_consumer():
    """Connects to RabbitMQ and starts consuming messages from the 'db_tasks' queue."""
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    
    queue = await channel.declare_queue("db_tasks", durable=True)
    
    print("RabbitMQ consumer started, waiting for messages...")
    await queue.consume(process_message)
    
    try:
        await asyncio.Future()
    finally:
        await connection.close()