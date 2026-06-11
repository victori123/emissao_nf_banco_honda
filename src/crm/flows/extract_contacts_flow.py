"""
Flow: Extract all contacts from the CRM and save to CSV.
Orchestrates: LoginPage → DashboardPage → ContactsPage → file_handler
"""
from selenium.webdriver.remote.webdriver import WebDriver
from src.crm.pages.login_page import LoginPage
from src.crm.pages.dashboard_page import DashboardPage
from src.crm.pages.contacts_page import ContactsPage
from src.shared.utils.file_handler import save_csv
from src.shared.utils.logger import get_logger
from src.shared.utils.retry import retry
from config.credentials import CRMCredentials
from config.settings import DATA_OUTPUT_DIR
from datetime import datetime

logger = get_logger(__name__)

@retry()
def run(driver: WebDriver) -> list[dict]:
    logger.info("=== START: extract_contacts_flow ===")

    # Step 1 – Login
    LoginPage(driver).open().login(CRMCredentials.USERNAME, CRMCredentials.PASSWORD)

    # Step 2 – Confirm dashboard loaded
    dashboard = DashboardPage(driver)
    assert dashboard.is_loaded(), "Dashboard did not load after login"
    dashboard.go_to_contacts()

    # Step 3 – Paginate and collect all contacts
    contacts_page = ContactsPage(driver)
    all_contacts: list[dict] = []

    while True:
        all_contacts.extend(contacts_page.extract_rows())
        if not contacts_page.has_next_page():
            break
        contacts_page.go_to_next_page()

    logger.info(f"Total contacts collected: {len(all_contacts)}")

    # Step 4 – Persist results
    output_path = DATA_OUTPUT_DIR / f"crm_contacts_{datetime.now():%Y%m%d_%H%M%S}.csv"
    save_csv(all_contacts, output_path)
    logger.info(f"Contacts saved to {output_path}")
    logger.info("=== END: extract_contacts_flow ===")

    return all_contacts
