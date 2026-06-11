from selenium.webdriver.remote.webdriver import WebDriver
from src.crm.pages.login_page import LoginPage
from src.crm.pages.main_page import MainPage
from src.crm.pages.crm_auto_page import CrmAutoPage
from src.shared.utils.file_handler import save_csv
from src.shared.utils.logger import get_logger
from src.shared.utils.retry import retry
from config.credentials import CRMCredentials
from config.settings import DATA_OUTPUT_DIR
from datetime import datetime

logger = get_logger(__name__)

@retry()
def run(driver: WebDriver) -> list[dict]:
    logger.info("=== START: extract_nfs_flow ===")

    # Step 1 – Login
    LoginPage(driver).open().login(CRMCredentials.USERNAME, CRMCredentials.PASSWORD)

    # Step 2 – Confirm main page loaded
    main_page = MainPage(driver)
    assert main_page.is_loaded(), "Main page did not load after login"
    main_page.go_to_crm_autos()

    # Step 3 – Navigate to Gerenciamento Menu
    crm_auto_page = CrmAutoPage(driver)
    assert crm_auto_page.is_loaded(), "Crm Auto page did not load"
    crm_auto_page.go_to_crm_autos()
    crm_auto_page.go_to_funil_vendas()
    crm_auto_page.search()

    all_nfs: list[dict] = []
    
    all_nfs.extend(crm_auto_page.extract_rows())

    logger.info(f"Total NFs collected: {len(all_nfs)}")

    # Step 4 – Persist results
    output_path = DATA_OUTPUT_DIR / f"crm_nfs_{datetime.now():%Y%m%d_%H%M%S}.csv"
    save_csv(all_nfs, output_path)
    logger.info(f"Nfs saved to {output_path}")
    logger.info("=== END: extract_nfs_flow ===")

    return all_nfs
