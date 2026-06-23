from pywinauto import Desktop, Application
from time import sleep
from src.shared.utils.logger import get_logger
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
import pyperclip

logger = get_logger(__name__)


class PrintNFPage:
    def __init__(self, window):
        self.window = window
        self.app = None

    def login_to_server(self, user: str, password: str, server: str):
        logger.info("Abrindo servidor de impressão: %s", server)

        try:
            self.window.set_focus()
            self.window.wait("ready", timeout=20)

            # Preencher campos de login seguindo o padrão do LoginPage
            panes = [p for p in self.window.children() if p.friendly_class_name() == "Pane"]
            edits = self.window.children(control_type="Edit")

            if edits:
                try:
                    edits[0].set_text('NBS')
                except Exception:
                    pass

            if len(panes) >= 2:
                panes[1].click_input()
                self.window.type_keys(user, with_spaces=True)
                panes[0].click_input()
                self.window.type_keys(password, with_spaces=True)

            edits[0].click_input()
            self.window.type_keys("{ENTER}")
            sleep(2)

            self.comunicado_click_sair("Notas Fiscais Ativas.*")

            new_window = Desktop(backend="uia").window(title_re=".*Nota Fiscal (Saída)*").handle
            app = Application(backend="uia").connect(handle=new_window)
            self.window = app.window(handle=new_window)

        except Exception:
            logger.error("Erro ao abrir/efetuar login no servidor de impressão", exc_info=True)
            raise

    def comunicado_click_sair(self, titulo_janela, timeout=20):
        desktop = Desktop(backend="win32")
        # Aguarda a janela aparecer
        janela = desktop.window(title_re=titulo_janela)
        janela.wait("visible enabled ready", timeout=timeout)
        janela.set_focus()
        botao_sair = janela.child_window(
            title="Sair",
        )
        botao_sair.wait("visible enabled ready", timeout=timeout)
        botao_sair.click_input()

        popup = Desktop(backend="uia").window(title_re=".*NBS-Controle de Notas.*")
        popup.wait("visible enabled ready", timeout=timeout)
        ok_button = popup.child_window(title="OK")
        ok_button.click_input()

        return True


    def close(self, force: bool = False):
        try:
            if self.window:
                try:
                    self.window.set_focus()
                    send_keys("%i")
                    sleep(2)
                    send_keys("%s")

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
            panes = self.window.descendants(control_type="Pane")
            if not panes:
                raise Exception("Campo de busca não encontrado na interface de impressão")

            campo_chassi = panes[27]
            campo_chassi.click_input()
            campo_chassi.type_keys(chassis, with_spaces=True)

            consultar_btn = None
            imprimir_nf = None

            for pane in self.window.descendants(control_type="Pane"):
                try:
                    rect = pane.rectangle()

                    # painel da direita
                    if (
                        1500 < rect.left < 1600 and
                        150 < rect.top < 250
                    ):
                        consultar_btn = pane
                    
                    if (
                        600 < rect.left < 700 and
                        800 < rect.top < 900
                    ):
                        imprimir_nf = pane


                except:
                    pass

            if consultar_btn:

                rect = consultar_btn.rectangle()

                width = rect.right - rect.left
                height = rect.bottom - rect.top

                x_rel = int(width / 2)
                y_rel = int(height * 0.20)

                consultar_btn.click_input(coords=(x_rel, y_rel))
                sleep(3)
                logger.info(f"Clicou em consultar")
            else:
                raise Exception("Botão consultar não encontrado")
            
            rect = imprimir_nf.rectangle()
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            x_rel = int(width * 0.30)
            y_rel = int(height * 0.40)
            imprimir_nf.click_input(coords=(x_rel, y_rel))
            
        except Exception:
            logger.error("Erro ao buscar chassi", exc_info=True)
            raise

    def navigate_second_screen_and_print(self, download_path, timeout=120):
        logger.info("Navegando segunda tela e iniciando impressão PDF")
        try:
            desktop = Desktop(backend="uia")
            # Aguarda a janela aparecer
            janela_danfe = desktop.window(title_re=".*Visualizar DANFE.*")
            janela_danfe.wait("visible enabled ready", timeout=timeout)
            janela_danfe.set_focus()
            list_btns = janela_danfe.descendants(control_type="Button")
            botao_imprimir = list_btns[8]
            botao_imprimir.click_input()
            
            desktop = Desktop(backend="win32")
            janela_imprimir = desktop.window(title_re=".*Imprimir.*")
            janela_imprimir.set_focus()
            send_keys("^a")
            sleep(2)
            send_keys("^m")
            sleep(2)
            ok_button = janela_imprimir.child_window(title="OK")
            ok_button.click_input()

            self._salvar_pdf(download_path)
            sleep(3)
            fechar_button = list_btns[-1]
            fechar_button.click_input()
            return "pdf_export_started"

        except Exception:
            logger.error("Erro durante navegação/impressão", exc_info=True)
            raise


    def _salvar_pdf(self, caminho_completo, timeout=20):
        desktop = Desktop(backend="win32")

        janela = desktop.window(title_re=".*Salvar.*")
        janela.wait("visible enabled ready", timeout=timeout)
        janela.set_focus()

        send_keys("%n")  # ALT + N (vai direto pro "Nome:")
        send_keys("^a{BACKSPACE}")
        pyperclip.copy(caminho_completo)  # copia com acentos para o clipboard
        sleep(1)
        send_keys("^v")
        sleep(1)
        send_keys("%l")

        return True