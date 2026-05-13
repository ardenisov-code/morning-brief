import os
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

def get_weather():
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        r = requests.get(url, params={
            "q": "Saint Petersburg,RU",
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "lang": "ru"
        }).json()
        temp = round(r["main"]["temp"])
        feels = round(r["main"]["feels_like"])
        desc = r["weather"][0]["description"].capitalize()
        wind = round(r["wind"]["speed"])
        humidity = r["main"]["humidity"]
        return f"🌤 <b>Погода в Питере:</b>\n{desc}, {temp}°C (ощущается {feels}°C)\nВетер {wind} м/с, влажность {humidity}%"
    except Exception as e:
        return f"🌤 Погода: ошибка ({e})"

def get_news(query, count=2):
    try:
        url = "https://newsapi.org/v2/everything"
        r = requests.get(url, params={
            "q": query,
            "language": "ru",
            "sortBy": "publishedAt",
            "pageSize": count,
            "apiKey": NEWS_API_KEY
        }).json()
        articles = r.get("articles", [])[:count]
        if not articles:
            r = requests.get(url, params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": count,
                "apiKey": NEWS_API_KEY
            }).json()
            articles = r.get("articles", [])[:count]
        if not articles:
            return "нет новостей"
        lines = []
        for a in articles:
            title = a["title"].split(" - ")[0].strip()
            link = a.get("url", "")
            lines.append(f"• {title}\n  <a href='{link}'>читать →</a>")
        return "\n".join(lines)
    except Exception as e:
        return f"ошибка: {e}"

def main():
    now = datetime.now()
    today = now.strftime("%d.%m.%Y")
    weekday = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"][now.weekday()]

    weather = get_weather()
    politics = get_news("политика Россия OR Кремль OR Путин", count=3)
    ai_news = get_news("искусственный интеллект OR artificial intelligence AI", count=2)
    telecom = get_news("телеком OR телекоммуникации OR Ростелеком OR МТС OR Билайн OR Мегафон", count=2)
    triathlon = get_news("triathlon OR ironman OR triathlete training swimming cycling running endurance", count=2)

    msg = f"""🌅 <b>Утренний бриф — {weekday}, {today}</b>

{weather}

━━━━━━━━━━━━━━━
🏛 <b>Политика:</b>
{politics}

━━━━━━━━━━━━━━━
🤖 <b>AI & технологии:</b>
{ai_news}

━━━━━━━━━━━━━━━
📡 <b>Телеком:</b>
{telecom}

━━━━━━━━━━━━━━━
🏊 <b>Триатлон:</b>
{triathlon}

━━━━━━━━━━━━━━━
📅 <b>Встречи:</b> подключим Google Calendar следующим шагом"""

    send_telegram(msg)
    print("Бриф отправлен!")

if __name__ == "__main__":
    main()
