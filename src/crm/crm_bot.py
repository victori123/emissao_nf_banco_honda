"""
CRM Bot entry point.
Manages the driver lifecycle and delegates to flows.
"""
from src.shared.browser.driver_factory import create_driver
from src.crm.flows import extract_nfs_flow
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)

def run_crm_bot() -> None:
    driver = create_driver()
    try:
        extract_nfs_flow.run(driver)
    except Exception as exc:
        logger.exception(f"CRM bot failed: {exc}")
        raise
    finally:
        driver.quit()
        logger.info("Browser closed")
