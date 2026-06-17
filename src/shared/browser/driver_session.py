from __future__ import annotations

from collections.abc import Callable
from selenium.webdriver.remote.webdriver import WebDriver
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)

class DriverSession:
    """Mutable browser session wrapper that can restart the underlying WebDriver."""

    def __init__(self, driver_factory: Callable[[], WebDriver]) -> None:
        self._driver_factory = driver_factory
        self._driver = driver_factory()

    def restart(self) -> None:
        logger.info("Restarting browser session")
        self.quit()
        self._driver = self._driver_factory()

    def quit(self) -> None:
        if self._driver is None:
            return

        try:
            self._driver.quit()
        except Exception as exc:
            logger.warning(f"Failed to quit browser session: {exc}")
        finally:
            self._driver = None

    def __getattr__(self, name: str):
        if self._driver is None:
            raise AttributeError(f"DriverSession has no active driver to access '{name}'")
        return getattr(self._driver, name)
