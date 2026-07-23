from pywinauto import Desktop, Application
from time import sleep
from src.shared.utils.logger import get_logger
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
import pyperclip
from pywinauto.mouse import click

logger = get_logger(__name__)


class PrintNFPage:
    def __init__(self, window):
        self.window = window
        self.app = None
        
    def is_logged(self):

        try:
            logger.info("Validando sucesso do login")

            # percorre toda a aplicação e não só a janela atual
            elements = self.window.app.windows()
   
            for el in elements:
                try:
                    name = el.element_info.name

                    if name and "Nota Fiscal (Saída)" in name:
                        logger.info("Login confirmado (NBS Nota Fiscal (Saída) encontrado)")
                        return True

                except Exception:
                    continue


            logger.warning("Nota Fiscal (Saída) não encontrado em nenhuma janela")
            return False

        except Exception as e:
            logger.error("Erro ao validar login", exc_info=True)
            return False


    def login_to_server(self, user: str, password: str, server: str):

        if self.is_logged():
            logger.info("Servidor já está aberto: %s", server)
            return

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
            sleep(3)
            mensagem, popup = self._capturar_mensagem_popup(title=".*Informa*")
            if mensagem and popup is not None:
                logger.info(f"Mensagem identificada: {mensagem}")
                ok_button = popup.child_window(title="OK")
                ok_button.click_input()

            self.comunicado_click_sair("Notas Fiscais Ativas.*")

            new_window = Desktop(backend="uia").window(title_re=".*Nota Fiscal (Saída)*").handle
            app = Application(backend="uia").connect(handle=new_window)
            self.window = app.window(handle=new_window)

        except Exception:
            logger.error("Erro ao abrir/efetuar login no servidor de impressão", exc_info=True)
            raise

    def comunicado_click_sair(self, titulo_janela, timeout=6):
        desktop = Desktop(backend="win32")
        # Aguarda a janela aparecer
        janela = desktop.window(title_re=titulo_janela)
        janela.wait("visible enabled ready", timeout=timeout)
        janela.set_focus()
        try:
            botao_sair = janela.child_window(
                title="Sair",
            )
            botao_sair.wait("visible enabled ready", timeout=timeout)
            botao_sair.click_input()
        except:
            pass
        
        sleep(2)
        self._click_ok_on_popup(".*NBS-Controle de Notas.*", timeout=timeout)

        return True

    def _click_ok_on_popup(self, title_re, timeout=6, retries=3):
        for tentativa in range(1, retries + 1):
            popup = None
            ok_button = None
            try:
                try:
                    popup = Desktop(backend="uia").window(title_re=title_re)
                    popup.wait("visible enabled ready", timeout=timeout)
                except Exception:
                    if 'NBS-Controle de Notas' in title_re:
                        janelas = Desktop(backend="win32").windows(
                            title_re='.*NBS-Controle de Notas.*'
                        )

                        popup = next(
                            w for w in janelas
                            if (
                                w.is_enabled()
                                and w.rectangle().width() > 0
                                and w.rectangle().height() > 0
                            )
                        )

                    else:
                        popup = Desktop(backend="win32").window(title_re=title_re)
                        popup.wait("visible enabled ready", timeout=timeout)

                popup.set_focus()

                ok_button = popup.child_window(title="OK", control_type="Button")
                ok_button.wait("visible enabled ready", timeout=timeout)

                try:
                    ok_button.click_input()
                except Exception:
                    # Alguns popups aceitam melhor click() ou ENTER do que click_input().
                    try:
                        ok_button.click()
                    except Exception:
                        popup.type_keys("{ENTER}")

                logger.info("Popup confirmado com sucesso (tentativa %s)", tentativa)
                return True

            except Exception:
                logger.warning(
                    "Falha ao confirmar popup '%s' na tentativa %s/%s",
                    title_re,
                    tentativa,
                    retries,
                    exc_info=True,
                )
                sleep(1)

        logger.warning("Nao foi possivel confirmar popup '%s' apos %s tentativas", title_re, retries)
        return False


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
                    if self.app is not None:
                        self.app.kill()
                except Exception:
                    pass

        except Exception:
            logger.error("Erro ao tentar fechar aplicação de impressão", exc_info=True)
            raise

    def limpar_filtro(self, pane):
        rect = pane.rectangle()

        largura = rect.right - rect.left
        altura = rect.bottom - rect.top

        x1 = rect.left + int(-20)
        y1 = rect.top + 5
        click(coords=(x1, y1)) # obtem a posição do campo e clica acima do campo
        sleep(1)

    def search_chassis(self, chassis: str):
        logger.info("Procurando chassi na interface de impressão: %s", chassis)
        try:
            self.window.set_focus()
            panes = self.window.descendants(control_type="Pane")
            edits = self.window.descendants(control_type="Edit")

            consultar_btn = panes[10]
            rect = consultar_btn.rectangle()
            width = rect.right - rect.left
            height = rect.bottom - rect.top    
            
            # click em limpar por posição  
            x_rel = int(width / 2)
            y_rel = int(height * 0.40)
            consultar_btn.click_input(coords=(x_rel, y_rel))

            # click em data inicial
            self.window.set_focus()
            data_hoje = panes[11]
            rect = data_hoje.rectangle()
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            x_rel = int(width / 3)
            y_rel = int(height * 0.10)
            data_hoje.click_input(coords=(x_rel, y_rel))
                        
            empresa_field = edits[2]
            self.limpar_filtro(empresa_field)
            if not panes:
                raise Exception("Campo de busca não encontrado na interface de impressão")

            campo_chassi = panes[27]
            campo_chassi.click_input()
            campo_chassi.type_keys(chassis, with_spaces=True)
            
            self.window.set_focus()
            combos = self.window.descendants(control_type="ComboBox")
            combo_filtros = combos[1]
            combo_filtros.select("10 - Autorizada")
            
            self.window.set_focus()
            combo_operacoes = edits[1]
            combo_operacoes.click_input()
            self.window.type_keys("Venda Veiculos Novos", with_spaces=True)
            self.window.type_keys("{ENTER}")

            #clicar em consultar por posição
            consultar_btn = panes[10]
            rect = consultar_btn.rectangle()
            width = rect.right - rect.left
            height = rect.bottom - rect.top  
            x_rel = int(width / 2)
            y_rel = int(height * 0.20)

            consultar_btn.click_input(coords=(x_rel, y_rel))
            sleep(3)
            logger.info(f"Clicou em consultar")

            imprimir_nf = panes[7]
            rect = imprimir_nf.rectangle()
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            x_rel = int(width * 0.30)
            y_rel = int(height * 0.40)
            imprimir_nf.click_input(coords=(x_rel, y_rel))
            mensagem_atencao = None
            try:
                mensagem_atencao, janela_atencao = self._capturar_mensagem_popup(title=".*Informação.*")
                if janela_atencao is not None:
                    ok_button = janela_atencao.child_window(title="OK")
                    ok_button.click_input()
            except:
                pass
            
            if mensagem_atencao:
                raise Exception(mensagem_atencao)
            
            logger.info(f"Chassi Encontrado")
            
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

    def _capturar_mensagem_popup(self, title):
            try:
                sleep(3)
                popup = Desktop(backend="uia").window(title_re=title)

                try:
                    popup.wait("visible", timeout=3)
                except:
                    popup = Desktop().window(title_re=title)
                    popup.wait("visible", timeout=3)

                popup.set_focus()
                wrapper = popup.wrapper_object()

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
                return "", None

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