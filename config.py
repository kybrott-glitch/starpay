import os

# ── Required ──────────────────────────────────────────────────────────────────
# Get from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Your Telegram user ID(s) — get yours from @userinfobot
# Add multiple admins: [123456789, 987654321]
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "YOUR_TELEGRAM_ID_HERE").split(",")
    if x.strip().isdigit()
]
