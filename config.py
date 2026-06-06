import os

# ── Required ──────────────────────────────────────────────────────────────────
# Get from @BotFather
BOT_TOKEN = os.getenv("8016460613:AAGc257gnXmeaYBz6I1jTtRnx9Qph1n6ofw", "8016460613:AAGc257gnXmeaYBz6I1jTtRnx9Qph1n6ofw")

# Your Telegram user ID(s) — get yours from @userinfobot
# Add multiple admins: [123456789, 987654321]
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("1899208318", "1899208318").split(",")
    if x.strip().isdigit()
]
