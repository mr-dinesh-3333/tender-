import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time
from datetime import datetime

# MongoDB connection
MONGO_URI = "mongodb+srv://dinesh2003:7386531980@cluster0.gaw7dkr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["govt_tenders"]
collection = db["eprocure_tenders"]

# Keywords to filter
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']

def scrape_tenders():
    print(f"\n⏱️ Starting new scraping cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
                print(f"⚠️ No listings found on page {page}")
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

                # Skip if tender exists
                if collection.find_one({"url": url}):
                    print(f"⏩ Already exists: {title[:50]}...")
                    continue

                # Keyword filtering
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
                    print(f"✅ Inserted: {title[:50]}...")
                else:
                    print(f"⛔ Skipped: {title[:50]}...")

            print(f"📄 Processed page {page}/{max_pages}")
            page += 1
            time.sleep(2)  # Be polite to the server

        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error: {e}")
        except Exception as e:
            print(f"❗ Unexpected error: {e}")
    
    print(f"✨ Scraping complete. Added {new_tenders} new tenders.")
    return new_tenders

# Continuous operation for Render
if __name__ == "__main__":
    print("🚀 Tender Scraper Service Started")
    while True:
        try:
            scrape_tenders()
            # Run every 6 hours (21600 seconds)
            print("😴 Sleeping for 6 hours...")
            time.sleep(21600)
        except KeyboardInterrupt:
            print("\n🛑 Service stopped by user")
            break
        except Exception as e:
            print(f"🔥 Critical error: {e}. Restarting in 5 minutes...")
            time.sleep(300)
