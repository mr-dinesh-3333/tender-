import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# 👉 Step 1: Filter Keywords
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']
page = 1

# 👉 Step 2: Email credentials (use app password)
EMAIL_SENDER = "gavinidineshkumar@gmail.com"
EMAIL_PASSWORD = "bmvg cggd yomw zmaf"  # App Password
EMAIL_RECEIVER = "gavinidineshkumar@gmail.com"


# 👉 Step 3: Improved Email function
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Use explicit TLS connection
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("📧 Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


# 👉 Step 4: Enhanced Scraping with error handling
found_tenders = False
while page <= 5:  # Safer loop condition
    print(f"📄 Processing page {page}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    params = {'page': str(page)}
    url = 'https://eprocure.gov.in/cppp/latestactivetenders'

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()  # Raise error for bad status

        if "Access Denied" in response.text:
            print("🚫 Access denied. Trying with cookies...")
            cookies = {'cookieWorked': 'yes'}
            response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=30)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find tender tables - updated selector
        tender_tables = soup.select('div.table-responsive table tbody')

        if not tender_tables:
            print(f"⛔ No tender tables found on page {page}. Exiting.")
            break

        for table in tender_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 6:
                    continue

                try:
                    # Updated element selection
                    link_cell = cells[0].find('a', href=True)
                    tender_name = link_cell.text.strip() if link_cell else ''
                    tender_url = link_cell['href'] if link_cell else ''

                    organisation_name = cells[5].text.strip()
                    publish_date = cells[1].text.strip()
                    closing_date = cells[2].text.strip()

                except Exception as e:
                    print(f"⚠️ Error parsing row: {e}")
                    continue

                # 👉 Step 5: Keyword matching
                if tender_name and any(keyword.lower() in tender_name.lower() for keyword in FILTER_KEYWORDS):
                    full_url = f"https://eprocure.gov.in{tender_url}" if tender_url else "URL not available"

                    print("\n✅ Tender Match Found:")
                    print(f"Title: {tender_name}")
                    print(f"Organisation: {organisation_name}")
                    print(f"Publish Date: {publish_date}")
                    print(f"Closing Date: {closing_date}")
                    print(f"URL: {full_url}")
                    print("-" * 40)

                    # 👉 Step 6: Send Email
                    subject = f"New Tender: {tender_name[:50]}"
                    body = f"""New Government Tender Found:

Title: {tender_name}
Organisation: {organisation_name}
Publish Date: {publish_date}
Closing Date: {closing_date}
URL: {full_url}
"""
                    if send_email(subject, body):
                        found_tenders = True

    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")
    except Exception as e:
        print(f"❗ Unexpected error: {e}")

    page += 1
    time.sleep(2)  # Be polite to the server

if not found_tenders:
    print("\nℹ️ No matching tenders found in all pages")
    send_email("Tender Scraper Report", "Scraper ran successfully but found no matching tenders.")
else:
    print("\n✨ Scraping completed successfully")
