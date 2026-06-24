from pywinauto.mouse import click
from pywinauto import Desktop, Application
from time import sleep
from pywinauto.keyboard import send_keys
from src.shared.utils.logger import get_logger
from src.shared.exceptions.rpa_exceptions import RPAException
import pyperclip
import pyperclip

logger = get_logger(__name__)

class RenaveEmissionPage:
    def __init__(self, window):
        self.window = window

    def clicar_renave(self):

        try:
            logger.info("Abrindo menu 'Renave'")

            menu_renave = self.window.child_window(
                title="Renave",
                control_type="MenuItem"
            )
            menu_renave.wait("visible", timeout=10)

            try:
                menu_renave.invoke()
            except Exception:
                menu_renave.click_input()

            submenu = self.window.child_window(
                title="Renave Zero KM",
                control_type="MenuItem",
                found_index=0
            )
            submenu.wait("visible", timeout=5)

            logger.info("Clicando em 'Renave Zero KM'")

            try:
                submenu.invoke()
            except Exception:
                submenu.click_input()


            logger.info("Validando abertura da tela 'Renave'")

            logger.info("Validando abertura da tela 'Renave'")

            desktop = Desktop(backend="uia")
            nova_janela = None

            for _ in range(20):
                for w in desktop.windows():
                    titulo = w.window_text()

                    if "Renave" in titulo:
                        if "zero km" in titulo.lower():
                            nova_janela = w
                            break

                if nova_janela:
                    break

            if not nova_janela:
                raise Exception("Janela 'Renave' não encontrada via UIA")

            logger.info(f"Janela encontrada: {nova_janela.window_text()}")

            self.window = Desktop(backend="uia").window(handle=nova_janela.handle)

            logger.info("Tela 'Renave Zero KM' aberta com sucesso")

        except Exception as e:
            logger.error(f"Erro ao clicar em 'Renave Zero KM': {e}")
            raise

    def validar_tabela_chassi(self, chassis: str) -> bool:
        try:
            logger.info("Validando dados da tabela via clipboard")

            #encontra o painel (fallback: pega qualquer panel visível)
            panels = self.window.descendants(control_type="Pane")

            if not panels:
                raise Exception("Nenhum painel encontrado")

            painel_tabela = panels[-2]

            if not painel_tabela:
                raise Exception("Painel da tabela não encontrado")

            #garante foco
            painel_tabela.click_input()

            sleep(0.5)
            painel_tabela.type_keys("^a")
            sleep(0.5)

            #copia
            painel_tabela.type_keys("^c")
            sleep(1)

            #lê clipboard
            texto = pyperclip.paste()

            if not texto.strip():
                raise Exception("Clipboard vazio")

            logger.info(f"Conteúdo copiado:\n{texto[:200]}")

            #verifica se só existe 1 ocorrência do chassi
            ocorrencias = texto.split('\r\n')[1:]

            logger.info(f"Ocorrências do chassi: {len(ocorrencias)}")

            return len(ocorrencias) == 1

        except Exception as e:
            logger.error(f"Erro ao validar tabela chassi: {e}")
            return False

    def _capturar_mensagem_popup_erro(self, title):
        try:
            sleep(3)
            popup = Desktop(backend="uia").window(title_re=title)

            try:
                popup.wait("visible", timeout=5)
            except:
                popup = Desktop().window(title_re=title)
                popup.wait("visible", timeout=5)

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

            return texto

        except Exception as e:
            return ""

    def limpar_filtro(self, pane):
        rect = pane.rectangle()

        largura = rect.right - rect.left
        altura = rect.bottom - rect.top

        x1 = rect.left + int(largura * 0)
        y1 = rect.top + int(-15)
        click(coords=(x1, y1)) # obtem a posição do campo e clica acima do campo
        sleep(1)


    def processar_operacao(self, chassis) -> str:
        try:
            logger.info(f"Preenchendo chassi: {chassis}")

            self.window.wait("visible", timeout=10)
            edits = self.window.descendants(control_type="Edit")
            empresa_estoque_atual = self.window.descendants(control_type="Pane")[2]
            situacao = self.window.descendants(control_type="Pane")[3]
            if not edits:
                raise Exception("Nenhum campo Edit encontrado")

            campo_chassi = edits[3]

            if not campo_chassi:
                raise Exception("Campo de chassi não encontrado")

            campo_chassi.click_input()
            campo_chassi.set_edit_text("")  # limpa
            campo_chassi.type_keys(chassis, with_spaces=True)
            self.limpar_filtro(empresa_estoque_atual)
            self.limpar_filtro(situacao)

            logger.info("Chassi preenchido")
            botao_pesquisar = self.window.child_window(
                title="Pesquisar",
                found_index=0
            )

            botao_pesquisar.wait("enabled", timeout=10)

            logger.info("Clicando em pesquisar")
            botao_pesquisar.click_input()

            if not self.validar_tabela_chassi(chassis):
                raise Exception("Erro pesquisa pelo chassis retornou mais de um registro")
            
            #encontra o painel (fallback: pega qualquer panel visível)
            panels = self.window.descendants(control_type="Pane")
            tabela_integracoes = panels[13]
            tabela_integracoes.click_input()
            sleep(0.5)
            #seleciona todos os registros
            tabela_integracoes.type_keys("^a")
            #copia
            tabela_integracoes.type_keys("^c")
            sleep(1)

            #lê clipboard
            linhas_tabela = pyperclip.paste()

            if not linhas_tabela:
                raise Exception("Erro ao obter linhas tabela integração")

            dados_encontrados = self._string_table_to_dict(linhas_tabela)

            dados_esperado = [
                {'Operação': 'Entrada Estoque', 'Status': 'Pendente'},
                {'Operação': 'Saída Venda', 'Status': 'Pendente'}
            ]

            if not all(
                any(item['Operação'] == v['Operação'] and item['Status'] == v['Status'] for item in dados_encontrados)
                for v in dados_esperado
            ):
                raise Exception(f'Entrada Estoque e/ou Saída Venda não localizados ou não estão com Status Pendente {dados_encontrados}')


            botao_operacao_selecionada = self.window.child_window(
                title="Processar Operação selecionada",
                found_index=0
            )
            logger.info("Clicando em operação selecionada")
            botao_operacao_selecionada.click_input()

            mensagem_erro = self._capturar_mensagem_popup_erro(title=".*Informação*")
            if mensagem_erro:
                raise Exception(mensagem_erro)
            
            return "OK"

        except Exception as e:
            logger.error(f"Erro ao processar operação: {e}")
            raise


    def _string_table_to_dict(self, text):
        linhas = text.split('\r\n')

        header = [h.strip() for h in linhas[0].split('\t')]

        resultado = []

        for linha in linhas[1:]:

            values = [v.strip() for v in linha.split('\t')]

            dicionario = dict(zip(header, values))
            resultado.append(dicionario)

        return resultado

