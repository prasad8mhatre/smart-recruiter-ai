import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(recipient_email: str, subject: str, message: str) -> bool:
    """Send email using SMTP."""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')

        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_sms(phone_number: str, message: str) -> bool:
    """Send SMS using Twilio."""
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER')

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False
