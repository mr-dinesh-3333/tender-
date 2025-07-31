from twilio.rest import Client

def send_whatsapp_alert(message):
    account_sid = "AC1ae038f3084933d8a95b12c5f70c6e7c"  # Your Twilio SID
    auth_token = "b11e46e3f8883673fef8dc35538a8d59"     # Your Twilio Token

    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
            body=message,
            from_="whatsapp:+14155238886",      # Twilio sandbox number
            to="whatsapp:+917386531980"          # YOUR verified WhatsApp number
        )
        print("✅ WhatsApp message sent:", message.sid)
    except Exception as e:
        print("❌ Failed to send WhatsApp alert:", e)
