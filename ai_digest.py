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
    return f"""Сегодня {today_str}. Ты — разведчик по практическим AI-находкам для читателя со следующим профилем:

Senior-коммерческий директор в крупном телеком-операторе, отвечает за макрорегион (большой P&L, команда, мультигородской охват). Основная работа: стратегическое планирование, оргдизайн, executive-презентации (McKinsey-style), анализ доли рынка, конкурентная разведка, переговоры (в т.ч. сложные — network sharing и подобное), речевая аналитика звонков с клиентами (сигналы оттока). Технически подкован — свободно работает в терминале, на Python, с API, держит локальные LLM (Qwen3/Llama через Ollama) на Mac с 8GB памяти. Активно занимается спортом на выносливость: бег (целевой темп ~4:00/км), плавание в открытой воде, велоспорт, кайтсёрфинг — использует Garmin и Magene, глубоко разбирается в тренировочных метриках, отслеживает восстановление (ЧСС, VO2max), интересуется добавками для выносливостных видов спорта. Ценит прямоту: если у находки есть подвох (не масштабируется, дорого, ограничено по железу, хайп без содержания) — это должно быть прямо сказано, а не замолчано.

ЖЁСТКИЙ СТОП-ФИЛЬТР: исключи находки уровня профессиональной софтверной инженерии — AST-графы, компиляторы, git-хуки, IDE-плагины, код-ревью тулинг, MCP-серверы для навигации по кодовой базе. Он не занимается разработкой ПО как профессией, поэтому такие находки не применимы, даже если технически ему понятны.

Найди через веб-поиск находки за последние 6 месяцев (не обязательно самые свежие по дате) — сортируй по "вау-эффекту" и реальной применимости к его работе/жизни, а не по хронологии. Источники: Reddit, X/Twitter, форумы, блоги практиков, YouTube-разборы. НЕ бери маркетинговые анонсы и общие обзоры "5 фич X" — только конкретные кейсы с результатом, которые кто-то реально попробовал и подтвердил.

Собери ДВА трека:

ТРЕК A — Claude / Claude Code / Cowork для управленческой работы и личной жизни: стратегия, executive-презентации, конкурентная разведка, оргдизайн, подготовка к переговорам, анализ рынка — а также тренировки на выносливость, анализ данных с носимых устройств (Garmin и т.п.), восстановление, здоровье, планирование быта.

ТРЕК B — автоматизация на локальных/open-source моделях (Qwen, DeepSeek, Kimi K2) + n8n: отчётность (Excel, Qlik Sense, SQL), речевая аналитика звонков (сигналы оттока), конкурентная разведка, интеграция с почтой/мессенджерами. Если находка про компактные квантованные модели, реально работающие на слабом железе (8-16GB) — это особенно ценно, он именно в таких условиях.

По каждому треку — максимум 3 находки, только реально впечатляющие и конкретные. Если по треку ничего подходящего не нашлось — пропусти его целиком, не выдумывай контент ради заполнения.

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
