from selenium.webdriver.common.by import By
from src.crm.pages.base_crm_page import BaseCRMPage

class DashboardPage(BaseCRMPage):
    """CRM dashboard — confirms successful login and provides navigation."""

    PATH = "/dashboard"

    _WELCOME_BANNER = (By.CSS_SELECTOR, ".welcome-banner")
    _NAV_CONTACTS   = (By.LINK_TEXT, "Contatos")

    def is_loaded(self) -> bool:
        return self.is_visible(*self._WELCOME_BANNER)

    def go_to_contacts(self) -> None:
        self.logger.info("Navigating to Contacts")
        self.click(*self._NAV_CONTACTS)
