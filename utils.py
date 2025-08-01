import logging
from twilio.rest import Client
import os

def send_whatsapp_alert(message):
    try:
        account_sid = os.getenv("TWILIO_SID", "AC1ae038f3084933d8a95b12c5f70c6e7c")
        auth_token = os.getenv("TWILIO_TOKEN", "b11e46e3f8883673fef8dc35538a8d59")
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=message,
            from_="whatsapp:+14155238886",
            to="whatsapp:+917386531980"
        )
        logging.info(f"WhatsApp message sent: {message.sid}")
        return True
    except Exception as e:
        logging.error(f"WhatsApp failed: {e}")
        return False
