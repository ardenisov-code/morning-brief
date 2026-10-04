#!/usr/bin/env python3
"""A five-evening, non-repeating self-development plan."""

import json
import os
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(__file__))
from evening_plan import SESSIONS_BY_WEEKDAY


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
HISTORY_PATH = Path("evening_history.json")
MSK = timezone(timedelta(hours=3))


# A five-evening plan is a focused sprint, not five unrelated consumption tasks.
# Each evening ends with a reusable artifact or a measurable decision.
WEEKLY_SPRINTS = (
    {
        "theme": "C-level fluency: platform economics",
        "days": (
            ("Платформенная карта", "Собери одну страницу: чем Avito, Ozon и hh.ru различаются по сторонам рынка, источнику ликвидности и главному риску роста.", "Готово, когда для каждого бизнеса есть: клиент, поставщик, network effect, north-star metric."),
            ("Юнит-экономика без словаря", "Возьми один заказ маркетплейса и разложи его contribution margin: GMV, take rate, логистика, платежи, promo, возвраты. Не используй чужие цифры без ссылки.", "Готово, когда можешь за 90 секунд объяснить, почему рост GMV не равен росту EBITDA."),
            ("Интервью-кейс", "Напиши ответ на вопрос: «Как за 90 дней поднять частоту успешных сделок в категории?» Сначала дерево гипотез, затем три метрики и один риск.", "Готово, когда ответ помещается на одну страницу и не содержит общих слов вроде “улучшить UX”."),
            ("AI-агент для управленца", "Составь 10 золотых вопросов для LLM-аналитика по P&L филиала: каждый вопрос должен иметь нужные поля, проверку и формат решения. Без реальных клиентских данных.", "Готово, когда любой аналитик поймёт, как проверить ответ агента на цифрах."),
            ("Триатлон: решение по нагрузке", "Сверь Garmin-отчёт, план недели и ощущения. Запиши одно решение: что сохранить, что снизить или что добавить на следующей неделе — и почему.", "Готово, когда решение опирается минимум на два сигнала: сон/HRV/readiness/TSB/RPE."),
        ),
    },
    {
        "theme": "C-level fluency: рост, доверие, execution",
        "days": (
            ("Рост без скидок", "Нарисуй дерево роста выручки классифайда: спрос, предложение, ликвидность, конверсия, повторные сделки, реклама. Выбери один рычаг и его побочный эффект.", "Готово, когда есть одна проверяемая гипотеза, а не список из десяти идей."),
            ("Trust & Safety как P&L", "Опиши один риск доверия в маркетплейсе или классифайде и его экономическую цепочку: событие → потеря ликвидности → деньги. Предложи одну продуктовую и одну операционную защиту.", "Готово, когда можешь назвать ведущую метрику, а не только NPS задним числом."),
            ("Партнёрская сделка", "Собери переговорную карту для партнёрства: интересы сторон, value exchange, экономика, стоп-факторы, первая пилотная метрика.", "Готово, когда есть письмо на одну страницу, которое можно отправить потенциальному партнёру."),
            ("AI: контур без утечки", "Выбери один закрытый управленческий процесс и опиши local-first workflow: входные данные, детерминированные проверки, роль локальной LLM, человеческое решение на выходе.", "Готово, когда схема не отправляет коммерческие или персональные данные во внешнюю модель."),
            ("Триатлон: техника как продукт", "Посмотри одну свежую видеозапись плавания или вспомни последнюю тренировку. Выбери ровно одну ошибку и одну проверку в воде на следующей сессии.", "Готово, когда проверку можно измерить: частота, количество гребков, положение головы или ощущение захвата."),
        ),
    },
    {
        "theme": "C-level fluency: деньги, narrative, личная система",
        "days": (
            ("P&L narrative", "Собери трёхминутный рассказ о своём P&L: исходная точка, один выбор, механизм результата, цифра, чему научился. Не перечисляй обязанности.", "Готово, когда рассказ звучит естественно без презентации."),
            ("Retail media", "Разложи рекламный бизнес платформы: кто платит, за какой инвентарь, где возникает конфликт с клиентским опытом, какие guardrails нужны.", "Готово, когда можешь назвать одну метрику рекламодателя и одну метрику клиента."),
            ("Разбор реальной роли", "Возьми одну сильную вакансию из радара и выпиши: P&L-мандат, три результата первых 90 дней, три твоих доказательства соответствия, один пробел и план его закрытия.", "Готово, когда это можно превратить в живое сообщение рекрутеру за пять минут."),
            ("AI: личный второй мозг", "Выбери один повторяющийся поток: заметки, встречи, вакансии или тренировки. Опиши вход, правило отбора, итоговый артефакт и еженедельный review.", "Готово, когда поток можно автоматизировать без потери контроля над решениями."),
            ("Восстановление как эксперимент", "На семь дней выбери один управляемый эксперимент со сном или восстановлением: например, стабильное время отбоя. Заранее зафиксируй метрику и порог успеха.", "Готово, когда в следующее воскресенье можно честно сказать: оставляю, меняю или отменяю."),
        ),
    },
)


def send_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}).encode()
    for attempt in range(1, 4):
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read()).get("ok", False)
        except Exception as exc:
            print(f"Telegram error (attempt {attempt}/3): {exc}", flush=True)
            if attempt < 3:
                time.sleep(15)
    return False


def load_history() -> list[dict[str, str]]:
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return [item for item in data.get("items", []) if isinstance(item, dict)]
    except (OSError, json.JSONDecodeError):
        return []


def save_history(history: list[dict[str, str]], sessions: list[tuple[date, dict[str, str]]]) -> None:
    items = [
        *history,
        *({"date": day.isoformat(), "title": session["title"], "topic": session["topic"]} for day, session in sessions),
    ]
    HISTORY_PATH.write_text(
        json.dumps({"items": items[-30:]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def choose_session(today: date, history: list[dict[str, str]]) -> dict[str, str]:
    pool = SESSIONS_BY_WEEKDAY[today.weekday()]
    recent_titles = {item.get("title") for item in history[-21:]}
    start = today.timetuple().tm_yday % len(pool)
    for offset in range(len(pool)):
        session = pool[(start + offset) % len(pool)]
        if session["title"] not in recent_titles:
            return session
    return pool[start]


def choose_sessions(today: date, history: list[dict[str, str]], count: int = 5) -> tuple[str, list[tuple[date, dict[str, str]]]]:
    """Return a weekly sprint built around durable priorities, not random topics."""
    sprint = WEEKLY_SPRINTS[today.isocalendar().week % len(WEEKLY_SPRINTS)]
    sessions = []
    for offset, (title, task, done) in enumerate(sprint["days"][:count]):
        day = today + timedelta(days=offset)
        sessions.append((day, {"topic": "Результат недели", "title": title, "task": task, "done": done}))
    return sprint["theme"], sessions


def response_text(payload: dict) -> str:
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")
    return ""


def build_ai_briefing(today: date, session: dict[str, str], history: list[dict[str, str]]) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    instructions = """Ты личный редактор вечернего часа саморазвития Артема Денисова.
Собери ОДНО короткое, содержательное сообщение в Telegram Markdown на русском, максимум 1 400 символов.
Не пересылай шаблонный план и не повторяй недавние темы. Артем -- senior product/business leader,
интересуется AI-практикой, карьерными возможностями и выносливым спортом. Не придумывай фактов о его дне.

Строгая структура:
🌙 *Вечерний час -- ДД.ММ*
*Тема: ...*
Почему сегодня: одно человеческое конкретное предложение.
*План на 30 минут*
1. ...
2. ...
3. ...
*Вопрос себе:* ...
*Материал:* [название](точный URL из задания), если URL дан. Если ссылки нет, не выдумывай её.

Используй задание как исходный материал, но адаптируй его к реальной пользе. Без общих мотивационных фраз,
без медицинских советов и без описания того, как устроен этот сервис."""
    context = {
        "date": today.strftime("%d.%m"),
        "today_session": session,
        "recent_sessions_do_not_repeat": history[-12:],
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": OPENAI_MODEL,
            "instructions": instructions,
            "input": json.dumps(context, ensure_ascii=False),
            "max_output_tokens": 700,
        },
        timeout=75,
    )
    response.raise_for_status()
    return response_text(response.json()).strip()


def fallback_briefing(today: date, session: dict[str, str]) -> str:
    lines = [
        f"🌙 *Вечерний час -- {today:%d.%m}*",
        f"*Тема: {session['topic']}*",
        f"*{session['title']}*",
        "*План на 30 минут*",
        f"1. {session['task']}",
        "2. Зафиксируй один вывод, который можно применить завтра.",
        "3. Закрой все рабочие вкладки и выбери одну следующую задачу на утро.",
        "*Вопрос себе:* Что из сегодняшнего действительно стоит повторить?",
    ]
    if session.get("material"):
        lines.append(f"*Материал:* {session['material']}")
    return "\n".join(lines)


def build_five_day_briefing(today: date, theme: str, sessions: list[tuple[date, dict[str, str]]]) -> str:
    labels = ("Сегодня", "Завтра", "Послезавтра", "День 4", "День 5")
    lines = [f"🌙 *Спринт на 5 вечеров — {today:%d.%m}–{sessions[-1][0]:%d.%m}*", f"*Фокус:* {theme}"]
    for label, (day, session) in zip(labels, sessions):
        lines.extend(
            [
                "",
                f"*{label}, {day:%d.%m} — {session['topic']}*",
                f"_{session['title']}_",
                session["task"],
                f"*Результат:* {session['done']}",
            ]
        )
    lines.extend(["", "*Правило:* 30–45 минут. Не переходи к следующему дню, пока не зафиксирован результат текущего."])
    return "\n".join(lines)


def main() -> None:
    today = datetime.now(MSK).date()
    history = load_history()
    theme, sessions = choose_sessions(today, history)
    if len(sessions) != 5:
        raise SystemExit("Could not build a complete five-evening plan")
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Starting five-evening plan", flush=True)
    briefing = build_five_day_briefing(today, theme, sessions)

    if not briefing:
        raise SystemExit("AI returned an empty evening briefing")
    ok = send_telegram(briefing)
    print(f"  Sent: {ok}", flush=True)
    if not ok:
        raise SystemExit("Telegram delivery failed")
    save_history(history, sessions)


if __name__ == "__main__":
    main()
