import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Browser ---
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
BROWSER = os.getenv("BROWSER", "chrome")          # chrome | firefox
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", 10))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", 30))

# --- CRM ---
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "https://crm.example.com")

# --- Logistics ---
LOGISTICS_BASE_URL = os.getenv("LOGISTICS_BASE_URL", "https://logistics.example.com")

# --- Paths ---
DATA_INPUT_DIR  = BASE_DIR / "data" / "input"
DATA_OUTPUT_DIR = BASE_DIR / "data" / "output"
LOGS_DIR        = BASE_DIR / "data" / "logs"

for d in (DATA_INPUT_DIR, DATA_OUTPUT_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Retry ---
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", 2.0))
