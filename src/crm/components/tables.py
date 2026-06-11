"""
Generic table extraction utilities shared across CRM pages.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

def extract_table(driver: WebDriver, table_selector: str) -> list[dict]:
    """
    Extract a standard HTML table into a list of dicts.
    The first <thead> row is used as dictionary keys.
    """
    table = driver.find_element(By.CSS_SELECTOR, table_selector)
    headers = [th.text.strip() for th in table.find_elements(By.CSS_SELECTOR, "thead th")]
    rows = []
    for tr in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
        cells = [td.text.strip() for td in tr.find_elements(By.TAG_NAME, "td")]
        if cells:
            rows.append(dict(zip(headers, cells)))
    return rows
