import os
from datetime import datetime, timezone, timedelta
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    if not r.ok:
        print("Telegram error:", r.text)


def build_prompt(today_str):
    return f"""Сегодня {today_str}. Ты — разведчик по практическим AI-находкам для коммерческого директора телеком-компании с большим штатом подчинённых.

Найди через веб-поиск находки за последние 6 месяцев (не обязательно самые свежие по дате) — сортируй по "вау-эффекту" и реальной применимости, а не по хронологии. Источники: Reddit (r/ClaudeAI, r/ClaudeCode, r/LocalLLaMA), X/Twitter, Hacker News, форумы, блоги практиков. НЕ бери маркетинговые анонсы и общие обзоры "5 фич X" — только конкретные кейсы с результатом, которые кто-то реально попробовал и подтвердил.

Собери ДВА трека:

ТРЕК A — Claude / Claude Code / Cowork: нестандартные приёмы, которые реально работают (агенты, skills, MCP-коннекторы, обходы лимитов, неочевидные паттерны использования).

ТРЕК B — автоматизация на open-source/локальных моделях (Qwen, DeepSeek, Kimi K2) + n8n + агенты: кейсы применения в бизнесе — автоматизация отчётности (Excel, Qlik Sense, выгрузки из SQL), речевая аналитика звонков с клиентами, интеграция с корпоративной почтой/мессенджерами. Аудитория — коммерческий директор, который может раздать это своей команде.

По каждому треку — максимум 3 находки. Если по треку ничего стоящего не нашлось — пропусти его целиком, не выдумывай контент ради заполнения.

Формат ответа — СТРОГО этот HTML-шаблон для Telegram (parse_mode=HTML), без markdown-разметки, без ``` оберток:

🅰️ <b>Claude / Cowork</b>

• <b>[Название находки]</b>
[1-2 предложения — что это и почему вау-эффект]
<a href="[URL]">источник</a>

(повторить для каждой находки трека A)

🅱️ <b>Внутренние модели / автоматизация</b>

• <b>[Название находки]</b>
[1-2 предложения]
<a href="[URL]">источник</a>

(повторить для каждой находки трека B)

Если трек пуст — не включай его заголовок вообще. Если оба трека пусты — верни ровно текст "ПУСТО" без ничего другого."""


def get_digest(today_str):
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-5.4",
            "tools": [{"type": "web_search"}],
            "input": build_prompt(today_str)
        },
        timeout=120
    )
    r.raise_for_status()
    data = r.json()

    out_texts = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    out_texts.append(c.get("text", ""))
    return "\n".join(out_texts).strip()


def main():
    now = datetime.now(timezone(timedelta(hours=3)))
    today = now.strftime("%d.%m.%Y")

    digest = get_digest(today)

    if not digest or digest.strip() == "ПУСТО":
        print("Сегодня без находок — ничего не отправляю")
        return

    header = f"💡 <b>AI-находки дня — {today}</b>\n\n"
    msg = header + digest

    if len(msg) > 4000:
        msg = msg[:3990] + "…"

    send_telegram(msg)

    os.makedirs("digests", exist_ok=True)
    with open(f"digests/{now.strftime('%Y-%m-%d')}.md", "w", encoding="utf-8") as f:
        f.write(f"# AI-находки — {today}\n\n{digest}\n")

    print("Дайджест отправлен и сохранён!")


if __name__ == "__main__":
    main()
