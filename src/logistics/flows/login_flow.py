from src.logistics.pages.login_page import LoginPage
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)
class LoginFlow:
    def __init__(self, window):
        self.page = LoginPage(window)

    def execute(self, user, password):

        logger.info("Starting login NBS")

        try:
            self.page.fill_user(user)
            self.page.fill_password(password)
            self.page.click_login()

            logger.info("Login successfully")

        except Exception as e:
            logger.error(f"Erro no login: {e}", exc_info=True)
            raise

