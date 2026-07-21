import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

# --- Browser ---
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
BROWSER = os.getenv("BROWSER", "chrome")          # chrome | firefox
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", 30))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", 120))

# --- CRM ---
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "http://crm.grupoaccampo.com.br")

# --- Logistics ---
LOGISTICS_BASE_SERVER = os.getenv("LOGISTICS_BASE_SERVER", r"C:\NBS\ger_veic")
LOGISTICS_NFS_SERVER = os.getenv("LOGISTICS_NFS_SERVER", r"C:\NBS\Nfvendas")

# --- Paths ---
DATA_INPUT_DIR  = BASE_DIR / "data" / "input"
DATA_OUTPUT_DIR = BASE_DIR / "data" / "output"
LOGS_DIR        = BASE_DIR / "data" / "logs"

for d in (DATA_INPUT_DIR, DATA_OUTPUT_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Retry ---
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", 2.0))
