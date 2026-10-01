#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI support bot: FAQ из файла + fallback на LLM (Groq, бесплатно).

- точные совпадения ищет в faq.json (быстро, бесплатно)
- если не нашло - спрашивает LLM с контекстом бизнеса
- диалоги пишет в dialogs.log
"""
import asyncio
import json
import logging
import os
import sys
import urllib.request

try:
    from aiogram import Bot, Dispatcher, F
    from aiogram.filters import CommandStart
    from aiogram.types import Message
except ImportError:
    print("Нужно: pip install -r requirements.txt")
    sys.exit(1)

TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
FAQ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faq.json")
BUSINESS = os.environ.get(
    "BUSINESS_INFO",
    "Небольшой магазин. Доставка 1-3 дня, возврат 14 дней, оплата картой и СБП.",
)

dp = Dispatcher()


def load_faq():
    try:
        with open(FAQ_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def find_faq(text, faq):
    t = text.lower()
    best, best_hit = None, 0
    for item in faq:
        hit = sum(1 for kw in item.get("keys", []) if kw.lower() in t)
        if hit > best_hit:
            best, best_hit = item, hit
    return best if best_hit else None


def ask_llm(question):
    """Ответ LLM с контекстом бизнеса. Пустая строка = нет ключа/сбой."""
    if not GROQ_KEY:
        return ""
    body = json.dumps({
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": f"Ты поддержка бизнеса. Отвечай коротко и по делу. О бизнесе: {BUSINESS}"},
            {"role": "user", "content": question[:800]},
        ],
        "max_tokens": 250, "temperature": 0.3,
    }).encode()
    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {GROQ_KEY}",
                     "Content-Type": "application/json",
                     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read().decode())
        return d["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.exception("llm fail: %s", e)
        return ""


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer("Привет! Я помощник. Спроси про доставку, оплату или возврат.")


@dp.message()
async def handle(m: Message):
    faq = load_faq()
    hit = find_faq(m.text or "", faq)
    if hit:
        await m.answer(hit["answer"])
        return
    ans = await asyncio.to_thread(ask_llm, m.text or "")
    await m.answer(ans if ans else "Передал вопрос оператору, ответим чуть позже.")
    try:
        with open("dialogs.log", "a", encoding="utf-8") as f:
            f.write(f"Q: {m.text}\nA: {(ans or 'operator')[:200]}\n---\n")
    except Exception:
        pass


async def main():
    if not TOKEN:
        print("Укажи токен: BOT_TOKEN=123:ABC python bot.py")
        sys.exit(1)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(Bot(TOKEN))


if __name__ == "__main__":
    main()
