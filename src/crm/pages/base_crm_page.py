from selenium.webdriver.remote.webdriver import WebDriver
from src.shared.browser.base_page import BasePage
from config.settings import CRM_BASE_URL

class BaseCRMPage(BasePage):
    """Adds CRM-specific helpers on top of BasePage."""

    BASE_URL = CRM_BASE_URL

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def full_url(self, path: str) -> str:
        return f"{self.BASE_URL.rstrip('/')}/{path.lstrip('/')}"
