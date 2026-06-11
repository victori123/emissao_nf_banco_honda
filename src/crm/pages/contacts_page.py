from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from src.crm.pages.base_crm_page import BaseCRMPage
from src.shared.exceptions.rpa_exceptions import DataExtractionException

class ContactsPage(BaseCRMPage):
    """CRM contacts list — search, filter, and extract contact data."""

    PATH = "/contacts"

    _SEARCH_INPUT  = (By.ID, "search-contacts")
    _TABLE_ROWS    = (By.CSS_SELECTOR, "table tbody tr")
    _NEXT_PAGE_BTN = (By.CSS_SELECTOR, "button.pagination-next")
    _NO_RESULTS    = (By.CSS_SELECTOR, ".no-results-message")

    def search(self, term: str) -> None:
        self.logger.info(f"Searching contacts for: '{term}'")
        self.fill(*self._SEARCH_INPUT, term)
        self.find(*self._SEARCH_INPUT).send_keys(Keys.ENTER)

    def extract_rows(self) -> list[dict]:
        if self.is_visible(*self._NO_RESULTS):
            return []

        rows = self.driver.find_elements(*self._TABLE_ROWS)
        if not rows:
            raise DataExtractionException("No rows found in contacts table.")

        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 4:
                data.append({
                    "name":    cols[0].text.strip(),
                    "email":   cols[1].text.strip(),
                    "phone":   cols[2].text.strip(),
                    "company": cols[3].text.strip(),
                })
        self.logger.info(f"Extracted {len(data)} contact(s) from current page")
        return data

    def has_next_page(self) -> bool:
        try:
            btn = self.driver.find_element(*self._NEXT_PAGE_BTN)
            return btn.is_enabled()
        except Exception:
            return False

    def go_to_next_page(self) -> None:
        self.click(*self._NEXT_PAGE_BTN)
