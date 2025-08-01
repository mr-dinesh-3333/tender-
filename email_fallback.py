import os
import requests
from bs4 import BeautifulSoup
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tender_scraper.log"),
        logging.StreamHandler()
    ]
)

# 👉 Step 1: Filter Keywords
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']
page = 1

# 👉 Step 2: Email credentials (use environment variables)
EMAIL_SENDER = os.getenv('SMTP_USER', 'gavinidineshkumar@gmail.com')  # Fallback to default
EMAIL_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # MUST be set in environment
EMAIL_RECEIVER = os.getenv('NOTIFICATION_EMAIL', 'gavinidineshkumar@gmail.com')

# 👉 Step 3: Enhanced Email function with detailed debugging
def send_email(subject, body):
    if not EMAIL_PASSWORD:
        logging.error("❌ SMTP password not configured! Using fallback file.")
        return False

    # Create message container
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    # Add headers to prevent spam filtering
    msg.add_header('Reply-To', EMAIL_SENDER)
    msg.add_header('Precedence', 'bulk')

    # Create secure SSL context
    context = ssl.create_default_context()
    last_error = None

    for attempt in range(3):  # Retry up to 3 times
        try:
            # Try method 1: SMTP_SSL (Port 465)
            logging.info(f"Attempt {attempt+1}: Trying SMTP_SSL (port 465)...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=15) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            logging.info("📧 Email sent successfully via SSL!")
            return True
        except Exception as e:
            last_error = e
            logging.error(f"❌ SMTP_SSL failed: {e}")
            time.sleep(2)  # Wait before retry

        try:
            # Try method 2: STARTTLS (Port 587)
            logging.info(f"Attempt {attempt+1}: Trying STARTTLS (port 587)...")
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            logging.info("📧 Email sent successfully via TLS!")
            return True
        except Exception as e:
            last_error = e
            logging.error(f"❌ STARTTLS failed: {e}")
            time.sleep(2)  # Wait before retry

    logging.error(f"❌ All email attempts failed. Last error: {last_error}")
    return False

# 👉 Step 4: Test email function immediately
if __name__ == "__main__":
    # Diagnostic info
    logging.info(f"Sender: {EMAIL_SENDER}")
    logging.info(f"Receiver: {EMAIL_RECEIVER}")
    logging.info(f"Password: {'*****' if EMAIL_PASSWORD else 'MISSING!'}")
    
    logging.info("Running email test...")
    test_body = f"Test email sent at {time.ctime()}\n"
    test_body += f"Sender: {EMAIL_SENDER}\nReceiver: {EMAIL_RECEIVER}"
    
    test_result = send_email("TENDER SCRAPER TEST", test_body)
    logging.info(f"Email test result: {'SUCCESS' if test_result else 'FAILURE'}")
    
    if not test_result:
        logging.error("Email test failed. Please check logs and credentials.")
        exit(1)
    logging.info("Email test successful. Starting scraping process...")

# ... [REST OF THE FILE REMAINS UNCHANGED] ...
