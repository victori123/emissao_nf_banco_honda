from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from config.settings import HEADLESS, BROWSER, IMPLICIT_WAIT, PAGE_LOAD_TIMEOUT

def create_driver() -> webdriver.Remote:
    """Factory: returns a configured WebDriver instance."""
    if BROWSER == "firefox":
        return _build_firefox()
    return _build_chrome()

def _build_chrome() -> webdriver.Chrome:
    opts = ChromeOptions()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=ChromeService(),
        options=opts,
    )
    _configure(driver)
    return driver

def _build_firefox() -> webdriver.Firefox:
    opts = FirefoxOptions()
    if HEADLESS:
        opts.add_argument("--headless")
    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()),
        options=opts,
    )
    _configure(driver)
    return driver

def _configure(driver: webdriver.Remote) -> None:
    driver.implicitly_wait(IMPLICIT_WAIT)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.maximize_window()
