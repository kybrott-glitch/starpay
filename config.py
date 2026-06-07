import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8931658637:AAG0oEYGZ0r-YZRxrlGfI2zJZzfJuJwOYb0")

# Multiple admins support
ADMIN_IDS: list[int] = [
    int(x.strip()) 
    for x in os.getenv("ADMIN_IDS", "1899208318,8045127644,515858240").split(",")
    if x.strip().isdigit()
]

print(f"Loaded {len(ADMIN_IDS)} admin(s): {ADMIN_IDS}")
