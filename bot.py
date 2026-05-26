import os
import json
import requests
from groq import Groq

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")
CHANNEL = "@ynwateam"

def get_posts():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    # Читаем через публичный канал используя RSS
    rss_url = f"https://rsshub.app/telegram/channel/ynwateam"
    response = requests.get(rss_url, timeout=10)
    
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    
    posts = []
    for item in root.findall('.//item')[:10]:
        title = item.find('title')
        description = item.find('description')
        if description is not None:
            posts.append(description.text or "")
    return posts

def analyze_post(text):
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{
            "role": "user",
            "content": f"""Ты аналитик футбольных новостей Ливерпуля.
Проанализируй пост и ответь ТОЛЬКО в JSON без лишнего текста:
{{"is_transfer": true/false, "summary": "краткое резюме если трансфер"}}

Пост: {text}"""
        }]
    )
    result = json.loads(response.choices[0].message.content)
    return result

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

def main():
    send_telegram("✅ Бот работает и проверяет трансферы!")

    try:
        posts = get_posts()
    except Exception as e:
        send_telegram(f"❌ Ошибка получения постов: {e}")
        return

    if not posts:
        return

    transfer_news = []
    for post in posts:
        try:
            result = analyze_post(post)
            if result.get("is_transfer"):
                transfer_news.append(result["summary"])
        except:
            continue

    if transfer_news:
        message = "🔴 <b>Трансферные новости Ливерпуля</b>\n\n"
        for news in transfer_news:
            message += f"• {news}\n\n"
        send_telegram(message)

main()
