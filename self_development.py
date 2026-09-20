#!/usr/bin/env python3
"""Evening self-development briefing."""

import json
import os
import sys
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from evening_plan import format_evening_block

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram(text: str) -> bool:
    import time
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()
    for attempt in range(1, 4):
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                return result.get("ok", False)
        except Exception as exc:
            print(f"Telegram error (attempt {attempt}/3): {exc}", flush=True)
            if attempt < 3:
                time.sleep(15)
    return False


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Starting evening briefing…", flush=True)
    briefing = format_evening_block(5)
    ok = send_telegram(briefing)
    print(f"  Sent: {ok}", flush=True)
    if not ok:
        raise SystemExit("Telegram delivery failed")


if __name__ == "__main__":
    main()
