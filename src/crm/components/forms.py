"""
Reusable form interactions for CRM pages.
Use these helpers when multiple pages share similar form patterns.
"""
from selenium.webdriver.common.by import By
from src.shared.browser.base_page import BasePage

def fill_date_picker(page: BasePage, field_id: str, date_str: str) -> None:
    """Fill a CRM date picker by id (format: YYYY-MM-DD)."""
    page.fill(By.ID, field_id, date_str)

def select_dropdown(page: BasePage, select_id: str, visible_text: str) -> None:
    from selenium.webdriver.support.ui import Select
    el = page.find(By.ID, select_id)
    Select(el).select_by_visible_text(visible_text)
