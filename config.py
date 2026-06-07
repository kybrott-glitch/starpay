import os

# ── Required ──────────────────────────────────────────────────────────────────
# Get from @BotFather
BOT_TOKEN = os.getenv("8931658637:AAG0oEYGZ0r-YZRxrlGfI2zJZzfJuJwOYb0", "8931658637:AAG0oEYGZ0r-YZRxrlGfI2zJZzfJuJwOYb0")

# Your Telegram user ID(s) — get yours from @userinfobot
# Add multiple admins: [123456789, 987654321]
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("1899208318", "1899208318").split(",")
    if x.strip().isdigit()
]
