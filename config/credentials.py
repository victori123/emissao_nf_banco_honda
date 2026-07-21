import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

class CRMCredentials:
    USERNAME: str = os.getenv("CRM_USERNAME", "")
    PASSWORD: str = os.getenv("CRM_PASSWORD", "")

class LogisticsCredentials:
    USERNAME: str = os.getenv("LOGISTICS_USERNAME", "")
    PASSWORD: str = os.getenv("LOGISTICS_PASSWORD", "")
    SERVER: str = os.getenv("LOGISTICS_SERVER", "")
    NFS_SERVER: str = os.getenv("LOGISTICS_NFS_SERVER", "")
