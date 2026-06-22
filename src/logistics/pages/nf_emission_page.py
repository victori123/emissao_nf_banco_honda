from pywinauto.mouse import click
from pywinauto import Desktop, Application
from time import sleep
from pywinauto.keyboard import send_keys
from src.shared.utils.logger import get_logger
from src.shared.exceptions.rpa_exceptions import RPAException
import pyperclip

logger = get_logger(__name__)

class NFEmissionPage:
    def __init__(self, window):
        self.window = window

    def dentro(self, v, alvo, tol):
        return (alvo - tol) < v < (alvo + tol)
    
    def emitir_nf(self):
        painel_botoes = None
        all = self.window.descendants()
        for pane in all:#self.window.descendants(control_type="Pane"):

            try:
                rect = pane.rectangle()
                largura = rect.right - rect.left
                altura = rect.bottom - rect.top

                if (
                    self.dentro(rect.left, 374, 60) and
                    self.dentro(rect.top, 803, 60) and
                    1100 < largura < 1300 and
                    40 < altura < 80
                ):
                    painel_botoes = pane
                    break
            except:
                pass


        if not painel_botoes:
             raise Exception("Botão 'Vender' não encontrado")
        
        self.clicar_vender(painel_botoes)
        
        popup = self.window.child_window(
            title="Informação",
            control_type="Window"
        )
        wrapper = popup.wrapper_object()
        mensagem = " ".join(
            t.window_text()
            for t in wrapper.descendants(control_type="Text")
            if t.window_text()
        )

        if "Atencao, voce esta vendendo Veiculo de outra empresa" in mensagem:
            popup.child_window(title="OK", control_type="Button").click_input()
            sleep(2)
            popup = self.window.child_window(
                title="Informação",
                control_type="Window"
            )
            wrapper = popup.wrapper_object()
            mensagem = " ".join(
                t.window_text()
                for t in wrapper.descendants(control_type="Text")
                if t.window_text()
            ) 

        if "A nota fiscal será emitida para o cliente" not in mensagem:
            raise Exception(mensagem)
        
        popup.child_window(title="OK", control_type="Button").click_input()
    
    def preencher_dados_nota_fiscal(self, ficha_observacao: str = "", ficha_codigo_cfop: str = ""):
        sleep(4)
        nova_handle = next((w.handle for w in Desktop(backend="win32").windows() if "Venda" in w.window_text()), None)  
        app = Application(backend="uia").connect(handle=nova_handle)
        self.window = app.window(handle=nova_handle)

        aba_corpo_nota_fiscal = None
        aba_dados_nota_fiscal = None
        aba_fechamento_observacao = None
        for ctrl in self.window.descendants():
            try:
                if 'Corpo da Nota Fiscal' in ctrl.element_info.name:
                    aba_corpo_nota_fiscal = ctrl

                if 'Dados da Nota Fiscal' in ctrl.element_info.name:
                    aba_dados_nota_fiscal = ctrl
                
                if 'Fechamento/Observação' in ctrl.element_info.name:
                    aba_fechamento_observacao = ctrl
            except:
                pass
        
        aba_corpo_nota_fiscal.click_input()
        sleep(2)
        
        painel_incluir = next(
            (
                p for p in self.window.descendants(control_type="Pane")
                if (
                    p.element_info.class_name == "TPanel" and
                    480 < p.rectangle().left < 520 and
                    350 < p.rectangle().top < 390 and
                    800 < (p.rectangle().right - p.rectangle().left) < 1200 and
                    40 < (p.rectangle().bottom - p.rectangle().top) < 100
                )
            ),
            None
        )
        self.window.set_focus()
        send_keys("{TAB 3}")
        send_keys("{UP 10}")
        send_keys("{ENTER}")
        send_keys("{UP}")
        pyperclip.copy(ficha_observacao)  # copia com acentos para o clipboard
        sleep(1)
        send_keys("^v") # Ctrl+V
        send_keys("{ENTER}")

        self.clicar_opcoes_incluir(painel_incluir, abaixo=True)

        aba_dados_nota_fiscal.click_input()
        
        observacao = next(
            (
                e for e in self.window.descendants(control_type="Edit")
                if (
                    e.element_info.class_name == "TDBEdit" and
                    580 < e.rectangle().left < 620 and
                    380 < e.rectangle().top < 420
                )
            ),
            None
        )
        
        if observacao:
            observacao.click_input()
            observacao.type_keys("^a{BACKSPACE}")  # limpa
            if ficha_observacao:
                observacao.type_keys(ficha_observacao, with_spaces=True)


        # Verificar o valor do CFOP, irá percorrer até encontrar o 5116
        panes = self.window.descendants(control_type="Pane")
        campo_cfop = panes[-2]
        
        campo_selecao_cfop = panes[-1]
        campo_selecao_cfop.click_input()
        self.window.set_focus()
        send_keys("{UP 20}")        
        
        # for para mudar cfop obter e verificar se é 5116, caso não seja, clicar no campo de seleção e ir para o próximo cfop
        for i in range(10):  # Limite de 10 tentativas para evitar loop infinito
            valor_cfop = campo_cfop.element_info.name
            if valor_cfop.strip() == ficha_codigo_cfop:
                break
            
            campo_selecao_cfop = self.window.descendants(control_type="Pane")[-1]
            campo_selecao_cfop.click_input()     
            self.window.set_focus()
            send_keys("{DOWN}")

            campo_cfop = self.window.descendants(control_type="Pane")[-2]

            if i == 9:  # Se chegar na última tentativa e não encontrar o CFOP desejado
                raise Exception(f"CFOP {ficha_codigo_cfop} não encontrado após 10 tentativas.")
        
        aba_fechamento_observacao.click_input()
        sleep(1)
        
        painel = self.window.child_window(title="Motivo Da Compra", control_type="Pane")
        campo = painel.child_window(control_type="Edit")

        campo.set_edit_text("Primeiro Ve¿culo ou Produto de For¿a")


    def clicar_opcoes_incluir(self, pane, acima=False, abaixo=False):
        rect = pane.rectangle()

        largura = rect.right - rect.left
        altura = rect.bottom - rect.top

        if acima:
            x1 = rect.left + int(largura * 0.20)
            y1 = rect.top + int(altura * 0.50)
            click(coords=(x1, y1))

        if abaixo:
            x2 = rect.left + int(largura * 0.70)
            y2 = rect.top + int(altura * 0.50)
            click(coords=(x2, y2))

    
    def clicar_vender(self, pane):
        rect = pane.rectangle()

        largura = rect.right - rect.left
        altura = rect.bottom - rect.top

        x = rect.left + int(largura * 0.80)
        y = rect.top + int(altura * 0.25)

        pane.click_input(coords=(x - rect.left, y - rect.top))

    def _capturar_mensagem_popup(self):
        try:
            popup = self.window.child_window(title="Informação", control_type="Window")
            wrapper = popup.wrapper_object()
            return " ".join(
                t.window_text().strip()
                for t in wrapper.descendants(control_type="Text")
                if t.window_text().strip()
            ), popup
        except Exception:
            return "", None

    @staticmethod
    def _is_success_message(mensagem: str) -> bool:
        texto = mensagem.strip()
        return texto.startswith("O.S número:") and texto.endswith("gerada com sucesso.")

    @staticmethod
    def _tem_erro(mensagem: str) -> bool:
        texto = mensagem.lower()
        palavras_erro = (
            "erro",
            "falha",
            "falhou",
            "não foi possível",
            "nao foi possivel",
            "não foi possivel",
            "não foi",
            "nao foi",
            "cancelado",
            "não autorizado",
            "nao autorizado"
        )
        return any(p in texto for p in palavras_erro)

    def confirmar(self):
        panes = self.window.descendants(control_type="Pane")

        panes_sorted = sorted(panes, key=lambda p: p.rectangle().top, reverse=True)

        confirmar_pane = None
        for pane in panes_sorted:
            try:
                rect = pane.rectangle()

                if rect.width() > 500 and rect.height() < 120:
                    confirmar_pane = pane
                    break
            except Exception:
                continue

        if confirmar_pane is None:
            raise RPAException("Painel de confirmação não encontrado")

        rect = confirmar_pane.rectangle()

        confirmar_pane.click_input(
            coords=(int(rect.width() * 0.12), int(rect.height() * 0.5))
        )
        sleep(3)

        janela = self.window.child_window(title="Imprimir")

        confirmar = janela.child_window(title="Confirmar", control_type="Button")
        confirmar.click_input()

        sleep(3)
        try:
            popup = self.window.child_window(title="Atenção!!!")
            popup.child_window(title="OK", control_type="Button").click_input()
        except Exception:
            pass

        mensagem, popup = self._capturar_mensagem_popup()
        if popup:
            popup.child_window(title="OK", control_type="Button").click_input()
        if not mensagem:
            return ""

        mensagem_os = " ".join(mensagem.split())

        if self._is_success_message(mensagem):
            mensagem, popup = self._capturar_mensagem_popup()
            if popup:
                popup.child_window(title="OK", control_type="Button").click_input()
            return mensagem_os

        if self._tem_erro(mensagem_os):
            raise RPAException(mensagem_os)

        raise RPAException(
            f"Mensagem inesperada após confirmação: {mensagem_os}"
        )


