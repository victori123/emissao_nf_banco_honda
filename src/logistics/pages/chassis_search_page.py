from src.shared.utils.logger import get_logger
from pywinauto import Desktop
from pywinauto import Desktop, Application

logger = get_logger(__name__)


class ChassisSearchPage:
    def __init__(self, window):
        self.window = window

    def _get_buttons(self):
        return self.window.descendants(control_type="Button")

    def _get_panes(self):
        return [
            p for p in self.window.descendants(control_type="Pane")
            if p.is_keyboard_focusable()
        ]

    def clicar_propostas(self):
        """
        Clica no menu 'Propostas'
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

            app = Application(backend="uia").connect(handle=nova_handle)
            self.window = app.window(handle=nova_handle)
            logger.info("Tela 'Propostas' aberta com sucesso")

        except Exception as e:
            logger.error(f"Erro ao clicar em 'Propostas': {e}")
            raise

    def search(self, chassis: str):
        try:
            logger.info(f"Iniciando busca por chassis {chassis}")
            
            regiao = self.window.child_window(
                title="Região",
                control_type="Pane"
            )
            self.window.click_input(coords=regiao.rectangle().mid_point())

            logger.info("Clicou em 'Região'")

            logger.info("Clicou em 'Região'")
            radio_chassi = self.window.child_window(
                title="Chassi",
                control_type="RadioButton"
            )

            radio_chassi.click_input()

            logger.info("Selecionou 'Chassi'")
            edits = self.window.descendants(control_type="Edit")

            if not edits:
                raise Exception("Nenhum campo Edit encontrado")

            campo_chassi = edits[0]  # ajuste se necessário

            campo_chassi.click_input()
            campo_chassi.type_keys(chassis, with_spaces=True, set_foreground=True)

            logger.info(f"Digitou o chassis: {chassis}")
            panes = self.window.descendants(control_type="Pane")

            if len(panes) < 5:
                raise Exception("Menos de 5 panes encontrados")

            consultar_btn = panes[4]  # índice 4 = 5º elemento

            consultar_btn.click_input()

            logger.info("Clicou em 'Consultar'")

        except Exception as e:
            logger.error(f"Erro na busca por chassis: {e}")
            raise