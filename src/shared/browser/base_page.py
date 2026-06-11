from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config.settings import IMPLICIT_WAIT
from src.shared.utils.logger import get_logger
from time import sleep

class BasePage:
    """Base class for all Page Objects (CRM and Logistics)."""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, IMPLICIT_WAIT)
        self.logger = get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    #  Navigation
    # ------------------------------------------------------------------ #
    def go_to(self, url: str) -> None:
        self.logger.info(f"Navigating to {url}")
        self.driver.get(url)

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    @property
    def title(self) -> str:
        return self.driver.title

    # ------------------------------------------------------------------ #
    #  Element helpers
    # ------------------------------------------------------------------ #
    def find(self, by: str, value: str) -> WebElement:
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def find_clickable(self, by: str, value: str) -> WebElement:
        return self.wait.until(EC.element_to_be_clickable((by, value)))

    def click(self, by: str, value: str) -> None:
        self.find(by, value).click()

    def fill(self, by: str, value: str, text: str) -> None:
        el = self.find_clickable(by, value)
        el.clear()
        el.send_keys(text)

    def text_of(self, by: str, value: str) -> str:
        return self.find(by, value).text

    def is_visible(self, by: str, value: str) -> bool:
        try:
            self.wait.until(EC.visibility_of_element_located((by, value)))
            return True
        except Exception:
            return False
        
    def js_click(self, by: str, value: str) -> None:
        el = self.find(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
        self.driver.execute_script("arguments[0].click();", el)

    def take_screenshot(self, name: str) -> None:
        from config.settings import LOGS_DIR
        from datetime import datetime
        path = LOGS_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{name}.png"
        self.driver.save_screenshot(str(path))
        self.logger.info(f"Screenshot saved: {path}")

    def switch_to_new_tab(self) -> None:
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def switch_to_tab(self, indice: int = 0) -> None:
        self.driver.switch_to.window(self.driver.window_handles[indice])

    def enable_and_click(self, by: str, value: str) -> None:
        el = self.find(by, value)
        self.driver.execute_script("arguments[0].classList.remove('p-disabled');", el)
        self.driver.execute_script("arguments[0].removeAttribute('disabled');", el)
        self.driver.execute_script("arguments[0].click();", el)

    def sleep_withou_condition(self, time_sleep:int)-> None:
        sleep(time_sleep)