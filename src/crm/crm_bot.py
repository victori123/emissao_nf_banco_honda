from src.shared.browser.driver_factory import create_driver
from src.shared.browser.driver_session import DriverSession
from src.crm.flows import extract_nfs_flow, attach_nfs_flow
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


def run_crm_bot() -> None:
    driver = DriverSession(create_driver)
    try:
        extract_nfs_flow.run(driver)
    except Exception as exc:
        logger.exception(f"CRM bot failed: {exc}")
        raise
    finally:
        driver.quit()
        logger.info("Browser closed")


def run_crm_attach_bot() -> None:
    driver = DriverSession(create_driver)
    try:
        attach_nfs_flow.run(driver)
    except Exception as exc:
        logger.exception(f"CRM attachment bot failed: {exc}")
        raise
    finally:
        driver.quit()
        logger.info("Browser closed")
