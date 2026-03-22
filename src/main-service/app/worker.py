import json
import aio_pika
from .config import settings
from .mailer import send_email_sync

async def email_consumer():
    """Waits for messages to expire from the delay queue and sends them."""
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()

    queue = await channel.declare_queue("send_emails", durable=True)
    await channel.declare_queue("db_tasks", durable=True)

    print("Main-Service: Waiting for scheduled emails...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body.decode())
                print(f"Sending email to {data['to']} now!")

                success = send_email_sync(data["to"], data["subject"], data["body"], is_html=data.get("is_html", True))
                status = "sent" if success else "failed"

                update_msg = {
                    "action": "update",
                    "user_id": data["user_id"],
                    "to": data["to"],
                    "subject": data["subject"],
                    "status": status
                }
                await channel.default_exchange.publish(
                    aio_pika.Message(body=json.dumps(update_msg).encode()),
                    routing_key="db_tasks"
                )