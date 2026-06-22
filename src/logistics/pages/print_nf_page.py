from pywinauto import Desktop, Application
from time import sleep
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class PrintNFPage:
    def __init__(self, window):
        self.window = window
        self.app = None

    def login_to_server(self, user: str, password: str, server: str):
        logger.info("Abrindo servidor de impressão: %s", server)

        # Dependendo do ambiente `server` pode ser o caminho do executável
        try:
            self.app = Application(backend="uia").start(server)
            self.window = self.app.window()
            self.window.wait("ready", timeout=20)

            # Preencher campos de login seguindo o padrão do LoginPage
            panes = [p for p in self.window.children() if p.friendly_class_name() == "Pane"]
            edits = self.window.children(control_type="Edit")

            if len(panes) >= 2:
                panes[1].click_input()
                self.window.type_keys(user, with_spaces=True)
                panes[0].click_input()
                self.window.type_keys(password, with_spaces=True)

            if edits:
                try:
                    edits[0].set_text(server)
                except Exception:
                    pass

            self.window.type_keys("{ENTER}")
            sleep(2)

        except Exception:
            logger.error("Erro ao abrir/efetuar login no servidor de impressão", exc_info=True)
            raise

    def close(self, force: bool = False):
        try:
            if self.window:
                try:
                    self.window.close()
                except Exception:
                    pass

            sleep(1)

            if force or (self.app is not None):
                try:
                    self.app.kill()
                except Exception:
                    pass

        except Exception:
            logger.error("Erro ao tentar fechar aplicação de impressão", exc_info=True)
            raise

    def search_chassis(self, chassis: str):
        logger.info("Procurando chassi na interface de impressão: %s", chassis)
        try:
            self.window.set_focus()
            edits = self.window.descendants(control_type="Edit")
            if not edits:
                raise Exception("Campo de busca não encontrado na interface de impressão")

            edits[0].set_edit_text(chassis)
            self.window.type_keys("{ENTER}")
            sleep(2)

        except Exception:
            logger.error("Erro ao buscar chassi", exc_info=True)
            raise

    def navigate_first_screen(self):
        logger.info("Navegando primeira tela para preparar impressão")
        # Implementação específica de navegação na primeira tela
        sleep(1)

    def navigate_second_screen_and_print(self):
        logger.info("Navegando segunda tela e iniciando impressão PDF")
        try:
            # procura botão que dispare exportação/impressão em PDF
            btn = None
            for b in self.window.descendants(control_type="Button"):
                try:
                    txt = b.window_text() or ""
                    if any(k in txt for k in ("Imprimir", "PDF", "Exportar", "Salvar")):
                        btn = b
                        break
                except Exception:
                    continue

            if not btn:
                raise Exception("Botão de imprimir/exportar não encontrado")

            btn.click_input()
            sleep(2)

            # lidar com diálogo de salvar/print (simplificado): aguardar e retornar sucesso
            return "pdf_export_started"

        except Exception:
            logger.error("Erro durante navegação/impressão", exc_info=True)
            raise
