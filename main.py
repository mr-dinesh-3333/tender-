import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB Atlas connection setup
# MongoDB Atlas connection setup
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://dinesh2003:7386531980@cluster0.gaw7dkr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["govt_tenders"]
collection = db["eprocure_tenders"]


collection = db['eprocure_tenders']

# Keywords to filter
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']

page = 1

while True:
    cookies = {
        'cookieWorked': 'yes',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    }

    params = {
        'page': f'{page}',
    }

    response = requests.get(
        'https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata',
        params=params,
        cookies=cookies,
        headers=headers,
    )

    soup = BeautifulSoup(response.content, 'html.parser')
    listing = soup.find_all('tbody')

    if not listing or page == 5:
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

        # 🔍 Keyword Filtering
        if any(keyword.lower() in title.lower() for keyword in FILTER_KEYWORDS):
            tender = {
                "title": title,
                "publish_date": publish_date,
                "close_date": close_date,
                "organisation": org_name,
                "url": url,
                "source": "eProcure"
            }
            collection.insert_one(tender)
            print(f"✅ Inserted: {title}")
        else:
            print(f"⛔ Skipped: {title}")

    page += 1
    print(f"--- Moving to Page {page} ---")
