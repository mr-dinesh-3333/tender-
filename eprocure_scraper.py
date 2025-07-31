import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

# ⬇️ Paste Groq summarizer function here
def summarize_tender(title, org, publish_date, close_date, url, api_key):
    prompt = f"""
Summarize this government tender in simple points:

Title: {title}
Organisation: {org}
Publish Date: {publish_date}
Closing Date: {close_date}
URL: {url}
"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes government tenders."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"❌ Error {response.status_code}: {response.text}"
