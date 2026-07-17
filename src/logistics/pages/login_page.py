from src.shared.utils.logger import get_logger
from pywinauto import Desktop
from time import sleep

logger = get_logger(__name__)

class LoginPage:
    def __init__(self, window):
        self.window = window

    def _capturar_mensagem_popup(self, title):
        try:
            popup = None
            sleep(3)
            popup = Desktop(backend="uia").window(title_re=title)

            try:
                popup.wait("visible", timeout=5)
            except:
                popup = Desktop().window(title_re=title)
                popup.wait("visible", timeout=5)

            wrapper = popup.wrapper_object()
            popup.set_focus()
            textos = []

            # 1. tenta pegar do próprio popup
            if popup.window_text().strip():
                textos.append(popup.window_text().strip())

            # 2. pega todos os descendentes
            for ctrl in wrapper.descendants():
                txt = ctrl.window_text().strip()
                if txt:
                    textos.append(txt)

            texto = " ".join(textos)
        
            return texto, popup

        except Exception as e:
            return "", ""

    def login(self, user, password, server):
        logger.info("Iniciando login (painéis detectados)")

        try:
            self.window.wait("ready", timeout=20)
            self.window.set_focus()

            # pega os painéis focáveis
            panes = [p for p in self.window.children() if p.friendly_class_name() == "Pane"]
            edits = self.window.children(control_type="Edit")

            logger.info(f"Encontrados {len(panes)} painéis")

            if len(panes) < 2:
                raise Exception("Não encontrou painéis suficientes")

            edits[0].set_text(server)
            logger.info("Server Preenchido")
            # Usuário
            panes[1].click_input()
            self.window.type_keys(user, with_spaces=True)

            logger.info("Usuário preenchido")

            # Senha
            panes[0].click_input()
            self.window.type_keys(password, with_spaces=True)

            logger.info("Senha preenchida")

            edits[0].click_input()
            self.window.type_keys("{ENTER}")

            logger.info("Login enviado com ENTER")

            mensagem, popup = self._capturar_mensagem_popup(title=".*Informação*")
            if mensagem:
                logger.warning(f"Mensagem identificada: {mensagem}")
                ok_button = popup.child_window(title="OK", control_type="Button")
                popup.set_focus()
                ok_button.click_input()
            

        except Exception as e:
            logger.error("Erro no login", exc_info=True)
            raise
