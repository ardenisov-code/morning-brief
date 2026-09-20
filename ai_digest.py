import os
import html
from datetime import datetime, timezone, timedelta
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AI_SYNTHESIS_WEEKDAY = int(os.getenv("AI_SYNTHESIS_WEEKDAY", "0"))  # Monday
FORCE_AI = os.getenv("FORCE_AI", "0").lower() in {"1", "true", "yes"}


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    r.raise_for_status()


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
            "model": OPENAI_MODEL,
            "tools": [{"type": "web_search"}],
            "max_output_tokens": 1200,
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


def get_fallback_digest():
    """Return recent practitioner links when paid AI synthesis is unavailable."""
    queries = ("Claude workflow", "local LLM", "AI automation n8n", "Garmin AI")
    hits = []
    seen = set()
    for query in queries:
        r = requests.get(
            "https://hn.algolia.com/api/v1/search_by_date",
            params={"query": query, "tags": "story", "hitsPerPage": 8},
            timeout=30,
        )
        r.raise_for_status()
        for item in r.json().get("hits", []):
            title = (item.get("title") or "").strip()
            url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}"
            if not title or url in seen:
                continue
            seen.add(url)
            hits.append((int(item.get("points") or 0), title, url))
    hits.sort(reverse=True)
    selected = hits[:6]
    if not selected:
        return "ПУСТО"
    lines = ["🛠 <b>Практические AI-кейсы</b>", ""]
    for _, title, url in selected:
        lines.extend([
            f"• <b>{html.escape(title)}</b>",
            f'<a href="{html.escape(url, quote=True)}">разбор / обсуждение практиков</a>',
            "",
        ])
    hf_items = get_huggingface_hits()
    if hf_items:
        lines.extend(["", "🤗 <b>Hugging Face: что сейчас набирает популярность</b>", ""])
        for title, url, detail in hf_items:
            lines.extend([
                f"• <b>{html.escape(title)}</b>",
                html.escape(detail),
                f'<a href="{html.escape(url, quote=True)}">Hugging Face</a>',
                "",
            ])
    lines.append("Подборка собрана напрямую из свежих публикаций и Hugging Face Hub.")
    return "\n".join(lines)


def get_huggingface_hits():
    """Pick practical items from the public HF trending APIs without paid AI."""
    items = []
    try:
        models = requests.get(
            "https://huggingface.co/api/models",
            params={"sort": "trendingScore", "direction": "-1", "limit": 20},
            timeout=30,
        )
        models.raise_for_status()
        useful_tags = {"text-generation", "image-text-to-text", "automatic-speech-recognition", "gguf"}
        for model in models.json():
            tags = set(model.get("tags") or [])
            if useful_tags.intersection(tags):
                model_id = model.get("id")
                detail = f"Трендовая модель; скачиваний: {model.get('downloads', 0):,}, лайков: {model.get('likes', 0)}."
                items.append((model_id, f"https://huggingface.co/{model_id}", detail))
                break

        spaces = requests.get(
            "https://huggingface.co/api/spaces",
            params={"sort": "trendingScore", "direction": "-1", "limit": 20},
            timeout=30,
        )
        spaces.raise_for_status()
        practical = ("agent", "pdf", "ocr", "audio", "video", "image", "qwen", "whisper", "llm")
        for space in spaces.json():
            space_id = space.get("id", "")
            if any(word in space_id.lower() for word in practical):
                detail = f"Трендовый интерактивный Space; лайков: {space.get('likes', 0)}. Можно проверить руками в браузере."
                items.append((space_id, f"https://huggingface.co/spaces/{space_id}", detail))
                break
    except Exception as e:
        print(f"Hugging Face source unavailable: {e}")
    return items[:2]


def main():
    now = datetime.now(timezone(timedelta(hours=3)))
    today = now.strftime("%d.%m.%Y")

    # Daily delivery stays useful and free; paid synthesis runs once a week.
    if (FORCE_AI or now.weekday() == AI_SYNTHESIS_WEEKDAY) and OPENAI_API_KEY:
        try:
            digest = get_digest(today)
        except Exception as e:
            print(f"OpenAI unavailable, using source fallback: {e}")
            digest = get_fallback_digest()
    else:
        print("Scheduled source-only day; skipping OpenAI")
        digest = get_fallback_digest()

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
