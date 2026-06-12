from src.logistics.pages.login_page import LoginPage
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)
class LoginFlow:
    def __init__(self, window):
        self.window = window
        self.page = LoginPage(window)

    def execute(self, user, password, server):
        logger.info("=== INÍCIO LOGIN FLOW ===")

        try:
            self.window.wait("ready", timeout=20)
            self.page.login(user, password, server)
            self.window.wait("ready", timeout=20)
            if not self.is_logged():
                raise Exception("Login não confirmado")

            logger.info("Login realizado com sucesso")

        except Exception as e:
            logger.error("Erro no LoginFlow", exc_info=True)
            raise

    def is_logged(self):

        try:
            logger.info("Validando sucesso do login")

            # percorre toda a aplicação e não só a janela atual
            elements = self.window.app.windows()
   
            for el in elements:
                try:
                    name = el.element_info.name

                    if name and "Gerência de Veículos" in name:
                        logger.info("Login confirmado (NBS Gerencia de Veiculos encontrado)")
                        return True

                except Exception:
                    continue


            logger.warning("NBS Gerencia de Veículos não encontrado em nenhuma janela")
            return False

        except Exception as e:
            logger.error("Erro ao validar login", exc_info=True)
            return False
