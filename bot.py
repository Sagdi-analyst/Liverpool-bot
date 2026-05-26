import os
import asyncio
import json
import requests
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta
from groq import Groq

# Настройки
TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")
CHANNEL = "ynwateam"

async def get_posts():
    client = TelegramClient("session", TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start()
    
    channel = await client.get_entity(CHANNEL)
    yesterday = datetime.now() - timedelta(hours=24)
    
    messages = await client(GetHistoryRequest(
        peer=channel,
        limit=50,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0
    ))
    
    posts = []
    for msg in messages.messages:
        if msg.date.replace(tzinfo=None) > yesterday and msg.text:
            posts.append(msg.text)
    
    await client.disconnect()
    return posts

def analyze_post(text):
    client = Groq(api_key=GROQ_API_KEY)
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{
            "role": "user",
            "content": f"""Ты аналитик футбольных новостей Ливерпуля.
Проанализируй пост и ответь ТОЛЬКО в JSON формате без лишнего текста:
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

async def main():
    posts = await get_posts()
    
    if not posts:
        send_telegram("📭 Новых трансферных новостей за последние 24 часа нет")
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

asyncio.run(main())
