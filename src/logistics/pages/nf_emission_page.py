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
        painel_botoes = all[0]

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
        
        app = Application(backend="uia").connect(title_re=".*Venda.*", timeout=15)
        dlg = app.window(title_re=".*Venda.*")
        dlg.wait("visible", timeout=15)

        #nova_handle = next((w.handle for w in Desktop(backend="win32").windows() if "Venda" in w.window_text()), None)  
        #app = Application(backend="uia").connect(handle=nova_handle)
        self.window = dlg

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
        painel_incluir = self.window.descendants(control_type="Pane")[-1]
        self.window.set_focus()
        send_keys("{TAB 3}")
        send_keys("{UP 10}")
        send_keys("{ENTER}")
        send_keys("{UP}")
        pyperclip.copy(ficha_observacao)  # copia com acentos para o clipboard
        sleep(1)
        send_keys("^v") # Ctrl+V

        self.clicar_opcoes_incluir(painel_incluir, abaixo=True)
        
        send_keys("+{TAB}")
        send_keys("{DOWN 3}")

        self.clicar_opcoes_incluir(painel_incluir, abaixo=True)

        aba_dados_nota_fiscal.click_input()
        observacao = self.window.descendants(control_type="Edit")[-1]
        
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

    def _capturar_mensagem_popup(self, title):
        try:
            sleep(3)
            popup = Desktop(backend="uia").window(title_re=title)

            try:
                popup.wait("visible", timeout=3)
            except:
                popup = Desktop().window(title_re=title)
                popup.wait("visible", timeout=3)

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


    @staticmethod
    def _is_success_message(mensagem: str) -> bool:
        texto = mensagem.strip()
        return texto.startswith("Informação OK O.S. número:") and texto.endswith("gerada com sucesso.")

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
        confirmar_pane = panes[-1]

        if confirmar_pane is None:
            raise RPAException("Painel de confirmação não encontrado")

        rect = confirmar_pane.rectangle()

        confirmar_pane.click_input(
            coords=(int(rect.width() * 0.12), int(rect.height() * 0.5))
        )

        mensagem_imprimir, janela_imprimir = self._capturar_mensagem_popup(title=".*Imprimir.*")       
        confirmar = janela_imprimir.child_window(title="Confirmar", control_type="Button")
        confirmar.click_input()
        logger.info(f"Clickou em confirmar na janela de impressão com a msg {mensagem_imprimir}")

        mensagem_atencao, janela_atencao = self._capturar_mensagem_popup(title=".*Atenção.*")
        ok_button = janela_atencao.child_window(title="OK")
        ok_button.click_input()
        logger.info(f"Clickou em OK na janela de Alerta com a msg {mensagem_atencao}")

        mensagem_os, janela_informacao_primeira = self._capturar_mensagem_popup(title=".*Informação*")
        ok_button = janela_informacao_primeira.child_window(title="OK")
        ok_button.click_input()
        logger.info(f"Clickou em OK na primeira janela de Informação com a msg {mensagem_atencao}")

        if self._is_success_message(mensagem_os):
            mensagem, janela_informacao_segunda = self._capturar_mensagem_popup(title=".*Informação*")
            ok_button = janela_informacao_segunda.child_window(title="Ok")
            ok_button.click_input()
            logger.info(f"Clickou em OK na segunda janela de Informação com a msg {mensagem}")
            return mensagem_os

        if self._tem_erro(mensagem_os):
            raise RPAException(mensagem_os)

        raise RPAException(
            f"Mensagem inesperada após confirmação: {mensagem_os}"
        )
