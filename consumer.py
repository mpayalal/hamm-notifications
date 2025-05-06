import os
import json
import asyncio
import logging
from aio_pika import connect_robust, IncomingMessage
from email_sender import send_email
from template_loader import render_template
from presigned_url import get_presigned_url 

rabbitmq_user = os.getenv("RABBITMQ_USER") 
rabbitmq_pass = os.getenv("RABBITMQ_PASSWORD")
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT")
rabbitmq_queue_notifications = os.getenv("RABBITMQ_QUEUE_NOTIFICATIONS")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_send_file(variables):
    file_path = variables.get("file_name", "")
    file_name = file_path.split("/")[-1]  # Solo el nombre del archivo
    file_url = get_presigned_url(file_path)

    context = {
        "client_name": variables.get("client_name"),
        "file_name": file_name,
        "file_url": file_url
    }
    return render_template("file_sent", context)

def handle_deleted_file(variables):
    file_path = variables.get("file_name", "")
    file_name = file_path.split("/")[-1]

    context = {
        "file_name": file_name
    }

    logger.info(context)
    return render_template("file_deleted", context)

def handle_file_authenticated(variables):

    context = {
        "file_name": variables.get("file_name")
    }

    logger.info(context)
    return render_template("file_authenticated", context)

async def handle_message(message: IncomingMessage):
    async with message.process():  # Ack automático
        try:
            payload = json.loads(message.body.decode())
            action = payload.get("action")
            variables = payload

            if action == "sendFile":
                logger.info("Recibido mensaje de send file")
                html_content = handle_send_file(variables)
                subject = "📦 Has recibido un archivo"
            elif action == "deletedFile":
                logger.info("Recibido mensaje de delete file")
                html_content = handle_deleted_file(variables)
                subject = "Confirmación de archivo eliminado"
            elif action == "fileAuthenticated": 
                logger.info("Recibido mensaje de autenticacion")
                html_content = handle_file_authenticated(variables)
                subject = "🔐 Documento autenticado"
            else:
                logger.error(f"Acción desconocida: {action}")
                return
            
            # Envío del correo
            to_email = variables.get("to_email")
            send_email(to_email=to_email, subject=subject, html_content=html_content)

        except json.JSONDecodeError:
            logger.error(f"Mensaje no es JSON válido: {message.body.decode()}")


async def start_consumer():
    try:
        connection = await connect_robust(
            host=rabbitmq_host,
            login=rabbitmq_user,
            password=rabbitmq_pass
        )
        logger.info("Conectado a Rabbit")

        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(rabbitmq_queue_notifications, durable=True)
        logger.info(f"Esperando mensajes en la cola: {rabbitmq_queue_notifications}")
        await queue.consume(handle_message)
        
        # Mantener vivo el consumidor
        await asyncio.Future()

    except Exception as e:
        logger.error(f"Error en el consumidor: {e}")
