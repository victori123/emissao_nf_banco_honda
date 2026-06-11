from selenium.webdriver.common.by import By
from src.crm.pages.base_crm_page import BaseCRMPage
from src.shared.exceptions.rpa_exceptions import LoginFailedException

class LoginPage(BaseCRMPage):
    """CRM login page interactions."""

    PATH = "/crm-auto"

    # Locators
    _USERNAME_INPUT = (By.XPATH, '//input[@placeholder="Usuário"]')
    _PASSWORD_INPUT = (By.XPATH, '//input[@placeholder="Senha"]')
    _SUBMIT_BTN     = (By.XPATH, '//button[.//span[text()="Acessar"]]')
    _ERROR_MSG      = (By.XPATH, '//div[contains(@class,"p-toast-summary") and contains(text(),"Verifique se as informações foram digitadas corretamente")]')

    def open(self) -> "LoginPage":
        self.go_to(self.full_url(self.PATH))
        return self

    def login(self, username: str, password: str) -> None:
        self.logger.info(f"Logging in as '{username}'")
        self.fill(*self._USERNAME_INPUT, username)
        self.fill(*self._PASSWORD_INPUT, password)
        self.click(*self._SUBMIT_BTN)

        if self.is_visible(*self._ERROR_MSG):
            msg = self.text_of(*self._ERROR_MSG)
            raise LoginFailedException(f"CRM login failed: {msg}")

        self.logger.info("Login successful")
