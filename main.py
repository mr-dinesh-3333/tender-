import os
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import time
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configuration from environment variables
EMAIL_SENDER = os.getenv('SMTP_USER')
EMAIL_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_RECEIVER = os.getenv('NOTIFICATION_EMAIL')
MONGO_URI = os.getenv('MONGODB_URI')
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tender_scraper.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting decorator
def rate_limit(max_per_minute):
    interval = 60 / max_per_minute
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            now = time.time()
            elapsed = now - wrapper.last_called if hasattr(wrapper, 'last_called') else interval
            if elapsed < interval:
                time.sleep(interval - elapsed)
            wrapper.last_called = time.time()
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Enhanced email function with retries
def send_email(subject, body, max_retries=3):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    context = ssl.create_default_context()
    last_exception = None

    for attempt in range(max_retries):
        try:
            # Try SSL first (port 465)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=10) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            logger.info("Email sent successfully via SSL")
            return True
        except Exception as e:
            last_exception = e
            logger.warning(f"SSL attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2 ** attempt)  # Exponential backoff

    logger.error(f"All email attempts failed. Last error: {str(last_exception)}")
    return False

# MongoDB connection with error handling
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, 
                           connectTimeoutMS=30000,
                           socketTimeoutMS=30000,
                           serverSelectionTimeoutMS=30000)
        client.admin.command('ping')  # Test connection
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        raise

# Keywords to filter tenders
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']

# Scraper function with enhanced error handling
@rate_limit(5)  # 5 requests per minute
def scrape_and_save_tenders():
    client = get_mongo_client()
    db = client["gov_tenders"]
    collection = db["eprocure_tenders"]
    
    # Create indexes if they don't exist
    collection.create_index([("url", 1)], unique=True)
    collection.create_index([("tender_name", "text")])

    all_data = []
    page = 1
    max_pages = 5
    new_tenders = 0
    found_keyword_tenders = False

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5'
    })

    while page <= max_pages:
        try:
            logger.info(f"Scraping page {page}")
            params = {'page': str(page)}
            response = session.get(
                'https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata',
                params=params,
                cookies={'cookieWorked': 'yes'},
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            listing = soup.find_all('tbody')

            if not listing:
                logger.info("No more tender listings found")
                break

            for data in listing:
                try:
                    cells = data.find_all('td')
                    if len(cells) < 6:
                        continue

                    tender_name = cells[0].find('a', {'title': 'External Url'}).text.strip() if cells[0].find('a') else ''
                    tender_url = cells[0].find('a')['href'] if cells[0].find('a') else ''
                    publish_date = cells[1].text.strip()
                    close_date = cells[2].text.strip()
                    org_name = cells[5].text.strip()

                    if collection.find_one({"url": tender_url}):
                        continue

                    record = {
                        "tender_name": tender_name,
                        "publish_date": publish_date,
                        "closing_date": close_date,
                        "organisation": org_name,
                        "url": tender_url,
                        "scraped_at": datetime.datetime.utcnow()
                    }

                    collection.insert_one(record)
                    new_tenders += 1
                    all_data.append(record)

                    # Check for keyword matches
                    if any(keyword.lower() in tender_name.lower() for keyword in FILTER_KEYWORDS):
                        found_keyword_tenders = True
                        email_body = f"""New Tender Found:
Title: {tender_name}
Organization: {org_name}
Published: {publish_date}
Closes: {close_date}
URL: https://eprocure.gov.in{tender_url}"""
                        send_email(f"New Tender: {tender_name[:50]}", email_body)

                except Exception as e:
                    logger.error(f"Error processing tender: {str(e)}")
                    continue

            page += 1
            time.sleep(5)  # Respectful delay between pages

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            break

    client.close()
    logger.info(f"Scraping complete. New tenders: {new_tenders}")
    
    if not found_keyword_tenders and new_tenders > 0:
        send_email(
            "Tender Scraper Report",
            f"Scraped {new_tenders} new tenders but none matched your keywords."
        )

    return all_data

# API Endpoints
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Government Tender Scraper",
        "version": "1.0.0"
    })

@app.route('/scrape', methods=['GET'])
def scrape_endpoint():
    try:
        data = scrape_and_save_tenders()
        return jsonify({
            "status": "success",
            "new_tenders": len(data),
            "data": data[:10]  # Return first 10 for demo
        })
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
