from pathlib import Path

from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from app.config import config
from app.schemas.email import EmailSchema

TEMPLATE_FOLDER = Path(__file__).resolve().parent / 'templates'

conn_config = ConnectionConfig(
    MAIL_USERNAME=config.EMAIL_HOST_USER,
    MAIL_PASSWORD=config.EMAIL_HOST_PASSWORD,
    MAIL_FROM=config.EMAIL_FROM,
    MAIL_PORT=config.EMAIL_PORT,
    MAIL_SERVER=config.EMAIL_HOST,
    MAIL_FROM_NAME=config.EMAIL_FROM_NAME,
    MAIL_SSL_TLS=True,
    MAIL_STARTTLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=TEMPLATE_FOLDER,
)


async def send_email(email: EmailSchema):
    message = MessageSchema(
        subject=email.subject,
        recipients=email.email,
        template_body=email.body,
        subtype=MessageType.html,
    )
    fm = FastMail(conn_config)
    await fm.send_message(message, template_name=email.template)


async def send_email_background(background_tasks: BackgroundTasks, email: EmailSchema):
    message = MessageSchema(
        subject=email.subject,
        recipients=email.email,
        template_body=email.body,
        subtype=MessageType.html,
    )
    fm = FastMail(conn_config)
    background_tasks.add_task(fm.send_message, message, template_name=email.template)
