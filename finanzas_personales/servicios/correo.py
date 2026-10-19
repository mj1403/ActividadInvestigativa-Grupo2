import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env

SERVIDOR_SMTP = "smtp.gmail.com"
PUERTO_SMTP = 465


def enviar_correo(destinatario, asunto, cuerpo_html):
    remitente = os.getenv("CORREO_REMITENTE")
    password = os.getenv("CORREO_PASSWORD")
    if not remitente or not password:
        raise ValueError("Faltan CORREO_REMITENTE o CORREO_PASSWORD en el .env")

    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content("Tu cliente de correo no muestra HTML.")
    mensaje.add_alternative(cuerpo_html, subtype="html")
    
    
    with smtplib.SMTP_SSL(SERVIDOR_SMTP, PUERTO_SMTP) as servidor:
        servidor.login(remitente, password)
        servidor.send_message(mensaje)