from src.shared.utils.logger import get_logger

logger = get_logger(__name__)

class LoginPage:
    def __init__(self, window):
        self.window = window

    
    def login(self, user, password, server):
        logger.info("Iniciando login (painéis detectados)")

        try:
            self.window.set_focus()
            self.window.wait("ready", timeout=20)

            # pega os painéis focáveis
            panes = [p for p in self.window.children() if p.friendly_class_name() == "Pane"]
            edits = self.window.children(control_type="Edit")

            logger.info(f"Encontrados {len(panes)} painéis")

            if len(panes) < 2:
                raise Exception("Não encontrou painéis suficientes")

            # Usuário
            panes[1].click_input()
            self.window.type_keys(user, with_spaces=True)

            logger.info("Usuário preenchido")

            # Senha
            panes[0].click_input()
            self.window.type_keys(password, with_spaces=True)

            logger.info("Senha preenchida")

            edits[0].set_text(server)

            logger.info("Server Preenchido")

            # enviar login
            self.window.type_keys("{ENTER}")

            logger.info("Login enviado com ENTER")

        except Exception as e:
            logger.error("Erro no login", exc_info=True)
            raise
