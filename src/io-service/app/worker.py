import asyncio
import json
import aio_pika
from sqlalchemy import select
from .database import AsyncSessionLocal
from .models import EmailLog
from .config import settings
from datetime import datetime

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = json.loads(message.body)
        print(f"Received DB task: {body}")

        action = body.get("action", "create")

        async with AsyncSessionLocal() as session:
            if action == "create":
                scheduled_str = body.get("scheduled_at")
                scheduled_dt = None
                if scheduled_str:
                    scheduled_dt = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
                
                new_log = EmailLog(
                    id_user=body.get("user_id"),
                    recipient=body.get("to"),
                    subject=body.get("subject"),
                    status="pending",
                    scheduled_at=scheduled_dt
                )
                session.add(new_log)
                await session.commit()
                print(f"Saved pending log for {body.get('to')}")

            elif action == "update":
                query = select(EmailLog).where(
                    EmailLog.id_user == body.get("user_id"),
                    EmailLog.recipient == body.get("to"),
                    EmailLog.subject == body.get("subject"),
                    EmailLog.status == "pending"
                ).order_by(EmailLog.id.desc()).limit(1)

                result = await session.execute(query)
                log = result.scalar_one_or_none()

                if log:
                    log.status = body.get("status")
                    await session.commit()
                    print(f"Updated log ID {log.id} to status: {log.status}")
                else:
                    print("Pending log not found for update!")

async def start_rabbitmq_consumer():
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    
    queue = await channel.declare_queue("db_tasks", durable=True)
    
    print("RabbitMQ DB consumer started, waiting for messages...")
    await queue.consume(process_message)
    
    try:
        await asyncio.Future()
    finally:
        await connection.close()