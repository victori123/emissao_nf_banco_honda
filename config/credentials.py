import os
from dotenv import load_dotenv

load_dotenv()

class CRMCredentials:
    USERNAME: str = os.getenv("CRM_USERNAME", "")
    PASSWORD: str = os.getenv("CRM_PASSWORD", "")

class LogisticsCredentials:
    USERNAME: str = os.getenv("LOGISTICS_USERNAME", "")
    PASSWORD: str = os.getenv("LOGISTICS_PASSWORD", "")
    SERVER: str = os.getenv("LOGISTICS_SERVER", "")
