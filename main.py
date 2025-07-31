from flask import Flask, jsonify
from bs4 import BeautifulSoup
from pymongo import MongoClient
import requests
import time
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
MONGO_URI = "mongodb+srv://dinesh2003:7386531980@cluster0.gaw7dkr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["govt_tenders"]
collection = db["eprocure_tenders"]

# Keywords to filter
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']

def scrape_tenders():
    print(f"\n⏱️ Scraping started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    page = 1
    max_pages = 5
    new_tenders = 0

    while page <= max_pages:
        try:
            cookies = {'cookieWorked': 'yes'}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            }
            params = {'page': str(page)}
            
            response = requests.get(
                'https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata',
                params=params,
                cookies=cookies,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            listing = soup.find_all('tbody')
            
            if not listing:
                break

            for data in listing:
                try:
                    title = data.find('a', {'title': 'External Url'}).text.strip()
                except:
                    title = ''
                try:
                    url = 'https://eprocure.gov.in' + data.find('a')['href']
                except:
                    url = ''
                try:
                    publish_date = data.find_all('td')[1].text.strip()
                except:
                    publish_date = ''
                try:
                    close_date = data.find_all('td')[2].text.strip()
                except:
                    close_date = ''
                try:
                    org_name = data.find_all('td')[5].text.strip()
                except:
                    org_name = ''

                if collection.find_one({"url": url}):
                    continue

                if any(keyword.lower() in title.lower() for keyword in FILTER_KEYWORDS):
                    tender = {
                        "title": title,
                        "publish_date": publish_date,
                        "close_date": close_date,
                        "organisation": org_name,
                        "url": url,
                        "source": "eProcure",
                        "timestamp": datetime.now()
                    }
                    collection.insert_one(tender)
                    new_tenders += 1

            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"❗ Error on page {page}: {e}")
            break

    print(f"✅ Scraping done. New tenders: {new_tenders}")
    return new_tenders

# Flask Routes
@app.route('/')
def home():
    return "✅ Government Tender Scraper is Live!"

@app.route('/tenders', methods=['GET'])
def run_scraper():
    try:
        count = scrape_tenders()
        return jsonify({"status": "success", "new_tenders_added": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Main entry
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
