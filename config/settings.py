import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
API_URL = os.getenv("API_URL", "http://localhost:8000")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Falta TELEGRAM_BOT_TOKEN")

if not DATABASE_URL:
    raise ValueError("Falta DATABASE_URL")