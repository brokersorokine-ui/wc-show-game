import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/wc_game")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
PAYMENT_AMOUNT = 100
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "2200 7000 0000 0000")
PAYMENT_SBP = os.getenv("PAYMENT_SBP", "+7 900 000-00-00")
PAYMENT_COMMENT_PREFIX = "CM-"
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))
SECRET_ADMIN_KEY = os.getenv("SECRET_ADMIN_KEY", "supersecret")