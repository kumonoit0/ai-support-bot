# AI Support Bot (aiogram 3.x + free LLM)

Support bot for a small business: answers from `faq.json` first
(fast, free), falls back to an LLM with business context when no
match. Dialogs go to `dialogs.log`.

## Run

```bash
pip install -r requirements.txt
BOT_TOKEN=123:ABC python bot.py
# with AI fallback (free Groq key):
BOT_TOKEN=123:ABC GROQ_API_KEY=gsk_... BUSINESS_INFO="..." python bot.py
```

Edit `faq.json` for your business. Without `GROQ_API_KEY` unknown
questions go to a human operator.
