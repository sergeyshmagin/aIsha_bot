import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL")  # например, http://localhost:8000
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Директория для хранения логов
LOG_DIR = os.getenv('LOG_DIR', 'logs')