from src.shared.utils.logger import get_logger
from pywinauto import Desktop, Application
from pywinauto.keyboard import send_keys
from time import sleep

logger = get_logger(__name__)


class ChassisSearchPage:
    def __init__(self, window):
        self.window = window
        self.original_window = window
        self.propostas_handle = None

    def _get_buttons(self):
        return self.window.descendants(control_type="Button")

    def _get_panes(self):
        return [
            p for p in self.window.descendants(control_type="Pane")
            if p.is_keyboard_focusable()
        ]

    def clicar_propostas(self):
        """
        Clica no menu 'Propostas' e troca para a nova janela que abre.
        """
        try:
            logger.info("Tentando clicar no menu 'Propostas'")

            menu_propostas = self.window.child_window(
                title="Propostas",
                control_type="MenuItem"
            )
            menu_propostas.wait("visible", timeout=10)

            try:
                menu_propostas.invoke()
            except Exception:
                menu_propostas.click_input()

            logger.info("Validando abertura da tela 'Propostas'")
            desktop_win32 = Desktop(backend="win32")
            nova_handle = None

            for _ in range(20):
                for w in desktop_win32.windows():
                    titulo = w.window_text()

                    if "Propostas" in titulo:
                        nova_handle = w.handle
                        break

                if nova_handle:
                    break

            if not nova_handle:
                raise Exception("Janela 'Propostas' não encontrada via win32")

            logger.info(f"Handle encontrado: {nova_handle}")

            self.propostas_handle = nova_handle
            app = Application(backend="uia").connect(handle=nova_handle)
            self.window = app.window(handle=nova_handle)
            logger.info("Tela 'Propostas' aberta com sucesso")

        except Exception as e:
            logger.error(f"Erro ao clicar em 'Propostas': {e}")
            raise

    
    def safe_get(self, lista, idx):
        try:
            return str(lista[idx].element_info.name).strip()
        except:
            return None


    def search(self, chassis: str)-> dict[any]:
        try:
            logger.info(f"Iniciando busca por chassis {chassis}")
            dados_encontrado = {}
            regiao_ctrl = {}        
            element_map = {}
            panes = self.window.descendants(control_type="Pane")
            for ctrl in self.window.descendants():
                try:
                    name = (ctrl.element_info.name or "").strip()
                    if name:
                        element_map[name] = ctrl
                    if 'Região' in ctrl.element_info.name:
                        regiao_ctrl = ctrl
                except:
                    pass
            
            regiao_ctrl.click_input()
            logger.info("Clicou em 'Região'")
            element_map["Chassi"].select()
            logger.info("Selecionou 'Chassi'")
            campo_pesquisa = panes[62]          
            campo_pesquisa.click_input()
            send_keys(str(chassis))
            logger.info(f"Digitou o chassis: {chassis}")

            consultar_btn = None

            for pane in self.window.descendants(control_type="Pane"):
                try:
                    rect = pane.rectangle()
                    # aproximação da posição do botão
                    if (
                        1400 < rect.left < 1500 and
                        700 < rect.top < 800
                    ):
                        consultar_btn = pane
                        break           
                except:
                    pass

            consultar_btn.click_input()
            logger.info("Clicou em 'Consultar'")
            sleep(3)
            todos = self.window.descendants()

            proposta_localizada = self.safe_get(todos, 9)

            if proposta_localizada != '0':

                dados_encontrado['proposta'] = self.safe_get(todos, 9)
                dados_encontrado['descricao_patio'] = self.safe_get(todos, 12)
                dados_encontrado['user'] = self.safe_get(todos, 13)
                dados_encontrado['modelo'] = self.safe_get(todos, 14)
                dados_encontrado['avaliacao'] = self.safe_get(todos, 15)
                dados_encontrado['data_validade'] = self.safe_get(todos, 16)
                dados_encontrado['data_emissao'] = self.safe_get(todos, 17)
                dados_encontrado['data_reserva'] = self.safe_get(todos, 18)

                logger.info(f"Proposta localizada {dados_encontrado}")
            
            else:
                raise Exception("Proposta não localizada para o chassis informado")

            return dados_encontrado        
    
        except Exception as e:
            self._close_propostas_window()
            raise
        # finally:
        #     pass
        #     #self._close_propostas_window()

    def _close_propostas_window(self):
        if not self.propostas_handle:
            return

        try:
            if self.window is not None and self.window != self.original_window:
                logger.info("Fechando janela 'Propostas' e retornando para a janela principal")
                self.window.close()

            self.window = self.original_window
            self.original_window.set_focus()
            self.propostas_handle = None

        except Exception as e:
            logger.warning(f"Falha ao fechar janela 'Propostas': {e}", exc_info=True)
            self.window = self.original_window
