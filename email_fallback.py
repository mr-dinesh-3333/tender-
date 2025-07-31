import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 👉 Step 1: Filter Keywords
FILTER_KEYWORDS = ['software', 'web development', 'web dev', 'AI', 'data entry', 'artificial intelligence']
page = 1

# 👉 Step 2: Email credentials
EMAIL_SENDER = "gavinidineshkumar@gmail.com"
EMAIL_PASSWORD = "bmvg cggd yomw zmaf"  # This is your App Password
EMAIL_RECEIVER = "gavinidineshkumar@gmail.com"  # You can change this to any other email

# 👉 Step 3: Email function
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            print("📧 Email sent successfully!")
    except Exception as e:
        print("❌ Email sending failed:", e)

# 👉 Step 4: Scraping Loop
while True:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Referer': 'https://eprocure.gov.in/',
    }

    params = {
        'page': str(page),
    }

    url = 'https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata'
    response = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    listings = soup.find_all('tbody')

    if not listings or page == 5:
        break

    for table in listings:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 6:
                continue

            try:
                tender_name = row.find('a', {'title': 'External Url'}).text.strip()
                tender_url = row.find('a')['href']
            except:
                tender_name = ''
                tender_url = ''

            organisation_name = cells[5].text.strip()
            publish_date = cells[1].text.strip()
            closing_date = cells[2].text.strip()

            # 👉 Step 5: Check if tender matches keywords
            if any(keyword.lower() in tender_name.lower() for keyword in FILTER_KEYWORDS):
                full_url = "https://eprocure.gov.in" + tender_url

                print("✅ Tender Match Found:")
                print("Title:", tender_name)
                print("Organisation:", organisation_name)
                print("Publish Date:", publish_date)
                print("Closing Date:", closing_date)
                print("URL:", full_url)
                print("-" * 40)

                # 👉 Step 6: Send Email
                subject = f"New Tender: {tender_name}"
                body = f"""
New Government Tender Found:

Title: {tender_name}
Organisation: {organisation_name}
Publish Date: {publish_date}
Closing Date: {closing_date}
URL: {full_url}
"""
                send_email(subject, body)

    page += 1
