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

# 👉 Step 2: Email credentials (use app password)
EMAIL_SENDER = "gavinidineshkumar@gmail.com"
EMAIL_PASSWORD = "bmvg cggd yomw zmaf"  # App Password
EMAIL_RECEIVER = "gavinidineshkumar@gmail.com"

# 👉 Step 3: Enhanced Email function with detailed debugging
def send_email(subject, body):
    # Create message container
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Create secure SSL context
    context = ssl.create_default_context()

    try:
        # Try method 1: SMTP_SSL (Port 465)
        logging.info("Trying SMTP_SSL (port 465)...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        logging.info("📧 Email sent successfully via SSL!")
        return True
    except Exception as e:
        logging.error(f"❌ SMTP_SSL failed: {e}")
        logging.info("Falling back to TLS...")

    try:
        # Try method 2: STARTTLS (Port 587)
        logging.info("Trying STARTTLS (port 587)...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        logging.info("📧 Email sent successfully via TLS!")
        return True
    except Exception as e:
        logging.error(f"❌ STARTTLS failed: {e}")
        return False

# 👉 Step 4: Test email function immediately
if __name__ == "__main__":
    logging.info("Running email test...")
    test_result = send_email("TENDER SCRAPER TEST", "This is a test email from the tender scraper.")
    logging.info(f"Email test result: {'SUCCESS' if test_result else 'FAILURE'}")
    if not test_result:
        logging.error("Email test failed. Please check logs and credentials.")
        exit(1)
    logging.info("Email test successful. Starting scraping process...")

# 👉 Step 5: Enhanced Scraping with error handling
found_tenders = False
while page <= 5:  # Safer loop condition
    logging.info(f"📄 Processing page {page}...")

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

        # Debugging: Save HTML for inspection
        with open(f"page_{page}.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        if "Access Denied" in response.text:
            logging.warning("🚫 Access denied. Trying with cookies...")
            cookies = {'cookieWorked': 'yes'}
            response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=30)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find tender tables - updated selector
        tender_tables = soup.select('div.table-responsive table tbody')

        if not tender_tables:
            logging.warning(f"⛔ No tender tables found on page {page}. Exiting.")
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
                    logging.error(f"⚠️ Error parsing row: {e}")
                    continue

                # 👉 Step 6: Keyword matching
                if tender_name and any(keyword.lower() in tender_name.lower() for keyword in FILTER_KEYWORDS):
                    full_url = f"https://eprocure.gov.in{tender_url}" if tender_url else "URL not available"

                    logging.info("\n✅ Tender Match Found:")
                    logging.info(f"Title: {tender_name}")
                    logging.info(f"Organisation: {organisation_name}")
                    logging.info(f"Publish Date: {publish_date}")
                    logging.info(f"Closing Date: {closing_date}")
                    logging.info(f"URL: {full_url}")
                    logging.info("-" * 40)

                    # 👉 Step 7: Send Email
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
                    else:
                        # Save email content to file as fallback
                        with open("failed_email.txt", "a") as f:
                            f.write(f"Subject: {subject}\n\n{body}\n\n{'='*50}\n")

    except requests.exceptions.RequestException as e:
        logging.error(f"🌐 Network error: {e}")
    except Exception as e:
        logging.error(f"❗ Unexpected error: {e}")

    page += 1
    time.sleep(5)  # Be polite to the server

if not found_tenders:
    logging.info("\nℹ️ No matching tenders found in all pages")
    send_email("Tender Scraper Report", "Scraper ran successfully but found no matching tenders.")
else:
    logging.info("\n✨ Scraping completed successfully")
