# ⬇️ Add these two lines at the VERY TOP ⬇️
import os
os.environ["PYTHONMALLOC"] = "malloc"  # Memory allocation fix
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import datetime
import logging
import time
# Replace email-related imports with:
from email_utils import send_email  # Adjust based on your functions  # Import WhatsApp function
from summarize import summarize_tender  # Import summarizer
import os

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tender_scraper.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI", "mongodb+srv://dinesh2003:7386531980@cluster0.gaw7dkr.mongodb.net/?retryWrites=true&w=majority"))
db = client["gov_tenders"]
collection = db["eprocure_tenders"]

# Keywords to filter tenders
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']

# GROQ API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")

def send_notification(subject, body):
    """Unified notification function with fallback"""
    # Try WhatsApp first
    whatsapp_msg = f"{subject}\n\n{body}"
    if send_whatsapp_alert(whatsapp_msg):
        logging.info("WhatsApp notification sent")
        return True
    
    logging.error("All notification methods failed")
    return False

def scrape_and_save_tenders():
    all_data = []
    page = 1
    new_tenders = 0
    found_keyword_tenders = False

    # Test notification service
    logging.info("Testing notification service...")
    if not send_notification("TENDER SCRAPER STARTED", "Scraping process initiated"):
        logging.error("Notification test failed! Check credentials.")
    
    while page <= 5:  # Limit to 5 pages
        try:
            logging.info(f"Scraping page {page}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            params = {'page': str(page)}
            url = 'https://eprocure.gov.in/cppp/latestactivetenders'
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tender_tables = soup.select('div.table-responsive table tbody')
            
            if not tender_tables:
                logging.info(f"No tenders found on page {page}")
                break
                
            for table in tender_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 6:
                        continue
                    
                    try:
                        link_cell = cells[0].find('a', href=True)
                        tender_name = link_cell.text.strip() if link_cell else ''
                        tender_url = link_cell['href'] if link_cell else ''
                        organisation = cells[5].text.strip()
                        publish_date = cells[1].text.strip()
                        closing_date = cells[2].text.strip()
                    except Exception as e:
                        logging.error(f"Error parsing row: {e}")
                        continue
                    
                    # Skip existing tenders
                    if collection.find_one({"url": tender_url}):
                        continue
                        
                    # Create record
                    record = {
                        "title": tender_name,
                        "publish_date": publish_date,
                        "closing_date": closing_date,
                        "organisation": organisation,
                        "url": tender_url,
                        "scraped_at": datetime.datetime.now()
                    }
                    
                    # Save to DB
                    collection.insert_one(record)
                    new_tenders += 1
                    
                    # Check for keyword matches
                    if tender_name and any(keyword.lower() in tender_name.lower() for keyword in FILTER_KEYWORDS):
                        found_keyword_tenders = True
                        full_url = f"https://eprocure.gov.in{tender_url}"
                        
                        # Generate AI summary
                        summary = summarize_tender(
                            tender_name, 
                            organisation,
                            publish_date,
                            closing_date,
                            full_url,
                            GROQ_API_KEY
                        )
                        
                        # Prepare notification
                        subject = f"🚀 New Tender: {tender_name[:50]}"
                        body = f"""📌 Title: {tender_name}
🏢 Organisation: {organisation}
📅 Publish Date: {publish_date}
⏳ Closing Date: {closing_date}
🔗 URL: {full_url}

📝 Summary:
{summary}
"""
                        send_notification(subject, body)
            
            page += 1
            time.sleep(2)  # Respectful delay
            
        except Exception as e:
            logging.error(f"Scraping error: {e}")
            break

    # Final report
    if not found_keyword_tenders:
        send_notification(
            "Tender Scraper Report",
            f"Scraped {new_tenders} new tenders but none matched your keywords."
        )
    
    logging.info(f"Scraping complete. New tenders: {new_tenders}")
    return {"status": "success", "new_tenders": new_tenders}

# Flask Routes
@app.route("/")
def home():
    return jsonify(scrape_and_save_tenders())

@app.route("/status")
def status():
    return jsonify({"status": "live", "timestamp": datetime.datetime.now().isoformat()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

