from selenium.webdriver.common.by import By
from src.crm.pages.base_crm_page import BaseCRMPage
from src.shared.exceptions.rpa_exceptions import LoginFailedException

class LoginPage(BaseCRMPage):
    """CRM login page interactions."""

    PATH = "/login"

    # Locators
    _USERNAME_INPUT = (By.ID, "username")
    _PASSWORD_INPUT = (By.ID, "password")
    _SUBMIT_BTN     = (By.CSS_SELECTOR, "button[type='submit']")
    _ERROR_MSG      = (By.CSS_SELECTOR, ".alert-error")

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
