from selenium.webdriver.common.by import By
from src.crm.pages.base_crm_page import BaseCRMPage

class MainPage(BaseCRMPage):
    """CRM Main — confirms successful login and provides navigation."""

    PATH = "/Main"

    _WELCOME_BANNER = (By.XPATH, '//*[@id="nbs-topo"]/div')
    _NAV_CRM_AUTOS   = (By.XPATH, '//div[contains(@class,"nbs-header") and contains(text(),"CRM Auto")]')

    def is_loaded(self) -> bool:
        return self.is_visible(*self._WELCOME_BANNER)

    def go_to_crm_autos(self) -> None:
        self.logger.info("Navigating to CRM Autos")
        self.click(*self._NAV_CRM_AUTOS)

        self.switch_to_new_tab()
