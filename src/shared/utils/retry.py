import time
import functools
from config.settings import MAX_RETRIES, RETRY_DELAY
from src.shared.exceptions.rpa_exceptions import MaxRetriesExceededException
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)

def retry(max_attempts: int = MAX_RETRIES, delay: float = RETRY_DELAY, exceptions=(Exception,)):
    """Decorator that retries a function on failure."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    logger.warning(f"[{func.__name__}] Attempt {attempt}/{max_attempts} failed: {exc}")
                    if attempt == max_attempts:
                        raise MaxRetriesExceededException(func.__name__, max_attempts) from exc
                    driver_candidate = kwargs.get("driver") if "driver" in kwargs else (args[0] if args else None)
                    if driver_candidate is not None and hasattr(driver_candidate, "restart") and callable(getattr(driver_candidate, "restart")):
                        logger.info(f"[{func.__name__}] Restarting driver before retry {attempt + 1}")
                        driver_candidate.restart()
                    time.sleep(delay)
        return wrapper
    return decorator
