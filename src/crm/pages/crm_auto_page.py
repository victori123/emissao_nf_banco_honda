import re
from selenium.webdriver.common.by import By
from src.crm.pages.base_crm_page import BaseCRMPage
from src.shared.exceptions.rpa_exceptions import DataExtractionException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from config.settings import IMPLICIT_WAIT

class CrmAutoPage(BaseCRMPage):
    """CRM Auto — confirms successful navigation."""

    PATH = "/crm-auto"

    _OPEN_MENU = (By.XPATH, '//*[@id="nbs-topo"]/div/div[2]/p-button/button/i')
    _NAV_AGENDA          = (By.XPATH, '//a[contains(@class,"p-panelmenu-header-link") and .//span[contains(text(),"Agenda")]]')
    _NAV_ESTOQUE         = (By.XPATH, '//a[contains(@class,"p-panelmenu-header-link") and .//span[contains(text(),"Estoque")]]')
    _NAV_GERENCIAMENTO   = (By.XPATH, '//a[contains(@class,"p-panelmenu-header-link") and .//span[contains(text(),"Gerenciamento")]]')
    _NAV_CENTRAIS        = (By.XPATH, '//a[contains(@class,"p-panelmenu-header-link") and .//span[contains(text(),"Centrais")]]')

    # Subitens (usam p-menuitem-link ao invés de p-panelmenu-header-link)
    _NAV_LEADS           = (By.XPATH, '//a[contains(@class,"p-menuitem-link") and .//span[contains(text(),"Leads")]]')
    _NAV_FUNIL_VENDAS    = (By.XPATH, '//a[contains(@class,"p-menuitem-link") and .//span[contains(text(),"Funil de Vendas")]]')

    _EMPRESA_FILTER = (By.XPATH, '//p-dropdown[contains(@class,"comboComboEmpresas")]//div[contains(@class,"p-dropdown-trigger")]')
    _X_CLEAR_DROPDOWN = (By.XPATH, "//i[contains(@class, 'p-dropdown-clear-icon') and contains(@class, 'pi-times')]")

    _ABA_PROPOSTA = (By.XPATH, "//span[contains(@class, 'p-tabview-title') and contains(text(), 'Proposta')]")
    _PESQUISAR = (By.ID, "btnPesquisar")
    _PAINEL_AGUARDANDO_NF = (By.XPATH, "//div[contains(@class,'p-panel-header')]//span[contains(text(),'Aguarda Emissão da Nota Fiscal')]")

    _TABLE_ROWS = (By.XPATH, "//*[@id='gbAguardaEmissaoNotaFiscal']//div[contains(@class,'lista-dados')]")

    _DIALOG_NEGOCIACAO = (By.XPATH, "/html/body/app-root/frm-tela-main/div[1]/nbs-topo/p-confirmdialog[1]/div/div/div[3]/button[1]/span[2]")

    _VEICULOS_DETAILS = (By.XPATH, 
        "//label[normalize-space()='VEÍCULO']"
        "/ancestor::div[contains(@class,'p-panel-header')]"
        "//button[contains(@class,'p-panel-toggler')]"
    )
    _FICHA_DETAILS = (By.XPATH, 
        "//div[contains(@class,'p-panel-header')][contains(.,'FICHA')]"
        "//button[contains(@class,'p-panel-toggler')]"
    )
    _NEGOCIACAO_DETAILS = (By.XPATH, 
        "//div[contains(@class,'p-panel-header')][contains(.,'NEGOCIAÇÃO')]"
        "//button[contains(@class,'p-panel-toggler')]"
    )

    _CLOSE_DATAILS = (By.XPATH, '//a[contains(@class,"nbs-tfpage-control")]')

    _OBSERVATION_DETAILS = (By.XPATH, '//*[@id="btnObservacao"]/button')

    _CLOSE_OBSERVATION = (By.XPATH, '//*[@id="sm-dialog"]/div/div/div[1]/div[2]/button')

    _PESQUISAR_EVENTO_LUPA = (By.XPATH, "//span[contains(@class,'pi-search')]")
    _CHASSI_CHECKBOX_BUTTON = (By.XPATH, '//label[@for="qf-flag-CHASSI_COMPLETO"]')
    _CHASSI_TEXT_FIELD = (By.XPATH, '//input-search//input[@type="text"]')
    _PESQUISAR_EVENTO_BUTTON = (By.XPATH, '//button[.//span[contains(@class,"pi-sync")]]')

    _MESA_FI_TAB = (
        By.XPATH,
        '//a[@role="tab"][.//span[contains(text(),"Mesa F&I")]]'
    )
    
    _DOCUMENTO_TAB = (
        By.XPATH,
        '//a[@role="tab"][.//span[normalize-space()="Documento"]]'
    )
        
    _INCLUIR_BUTTON = (
        By.XPATH,
        '//p-button[.//span[normalize-space()="Incluir"]]//button'
    )
    
    _SALVAR_BUTTON = (
        By.XPATH,
        '//p-button[@id="btnSalvar"]//button'
    )
    
    def is_loaded(self) -> bool:
        return self.find(*self._OPEN_MENU)

    def go_to_crm_autos(self) -> None:
        self.logger.info("Navigating to CRM Autos")
        self.click(*self._NAV_GERENCIAMENTO)

    def go_to_funil_vendas(self) -> None:
        self.click(*self._NAV_FUNIL_VENDAS)

    def clean_empresa(self)-> None:
        elemento = self.find(*self._X_CLEAR_DROPDOWN)            
        self.driver.execute_script("arguments[0].click();", elemento)

    def search(self)-> bool:
        self.clean_empresa()
        self.click(*self._PESQUISAR)
        self.sleep_withou_condition(6)
        self.click(*self._ABA_PROPOSTA)
        self.click(*self._PAINEL_AGUARDANDO_NF)

    def attach_pdf_to_current_opportunity(self, pdf_path: str, chassi: str, numero_evento: str) -> None:
        self.logger.info("Attachment step for path: %s", pdf_path)
        self.click(*self._PESQUISAR_EVENTO_LUPA)
        self.click(*self._CHASSI_CHECKBOX_BUTTON)
        self.fill(*self._CHASSI_TEXT_FIELD, chassi)
        self.click(*self._PESQUISAR_EVENTO_BUTTON)

        self.clicar_evento_grid(numero_evento=numero_evento)

        self.js_click(*self._NEGOCIACAO_DETAILS)

        self.click(*self._MESA_FI_TAB)

        self.click(*self._DOCUMENTO_TAB)

        self.click(*self._INCLUIR_BUTTON)

        
        dropdown = self.wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//label[normalize-space()="Tipo Documento"]/ancestor::span//div[contains(@class,"p-dropdown")]'
            )))

        self.driver.execute_script("arguments[0].click();", dropdown)

        # 2. Aguardar opções aparecerem
        opcao = self.wait.until(EC.element_to_be_clickable((
            By.XPATH,
            f'//li[@role="option"]//span[normalize-space()="Nota Fiscal"]'
        )))

        self.driver.execute_script("arguments[0].click();", opcao)
        
        self.enviar_documento(pdf_path)

        self.click(*self._SALVAR_BUTTON)
        
        return "Sucesso"

    def enviar_documento(self, caminho_arquivo, timeout=10):

        
        input_file = self.wait.until(EC.presence_of_element_located((
                By.ID, "docfile"
            )))

            # Garante visibilidade para evitar erro
        self.driver.execute_script("""
            arguments[0].style.display = 'block';
            arguments[0].style.visibility = 'visible';
            arguments[0].style.opacity = 1;
        """, input_file)

        input_file.send_keys(caminho_arquivo)

        self.logger.info("Arquivo enviado com sucesso.")


    def _safe_get_text(self, xpath, by=By.XPATH):
        try:
            el = self.driver.find_element(by, xpath)
            return el.text.strip()
        except:
            return None

    def _safe_get_text_element_on_memory(self, item, by, xpath):
        try:
            return item.find_element(by, xpath).text.strip()
        except:
            return None

    def extrair_dados_ficha(self)-> dict[any]:
        dados = {}
        #expand details
        if self.is_visible(*self._DIALOG_NEGOCIACAO):
            self.click(*self._DIALOG_NEGOCIACAO)

        try:
            self.find_clickable(*self._VEICULOS_DETAILS)
            self.js_click(*self._VEICULOS_DETAILS)
            self.js_click(*self._FICHA_DETAILS)
            self.js_click(*self._NEGOCIACAO_DETAILS)
        except:
            pass

        # ── CABEÇALHO ────────────────────────────────────────────────────
        dados["nome_evento"] = self._safe_get_text(
            "//div[contains(@class,'client-name')]//label"
        )
        dados["codigo_evento"] = self._safe_get_text(
            "//label[contains(@class,'copy-event-code')]"
        )

        # ── LEAD ─────────────────────────────────────────────────────────
        lead_base = "//frm-detalhes-lead-dados"

        dados["lead_email"] = self._safe_get_text( f"{lead_base}//*[contains(@class,'pi-envelope')]/following::label[1]"
        )
        dados["lead_whatsapp"] = self._safe_get_text( f"{lead_base}//*[contains(@class,'pi-whatsapp')]/following::label[1]"
        )
        dados["lead_telefone"] = self._safe_get_text( f"{lead_base}//*[contains(@class,'pi-phone')]/following::label[1]"
        )
        dados["lead_cpf"] = self._safe_get_text(
            f"{lead_base}//label[contains(text(),' CPF ')]/following::label[1]"
        )
        dados["lead_proprietario"] = self._safe_get_text(
            f"{lead_base}//label[contains(@class,'LblMudarDescClienteProprietario')]/preceding::label[1]"
        )
        dados["lead_classe"] = self._safe_get_text(
            f"{lead_base}//label[contains(text(),' Classe ')]/following::label[1]"
        )

        # ── VEÍCULO ──────────────────────────────────────────────────────
        veiculo_base = "//frm-detalhes-veiculo-dados"

        campos_veiculo = {
            "veiculo_modelo":       "Modelo",
            "veiculo_ano_mod":      "Ano/Mod",
            "veiculo_linha":        "Linha",
            "veiculo_interesse":    "Interesse",
            "veiculo_origem":       "Origem",
            "veiculo_cor":          "Cor",
            "veiculo_combustivel":  "Combustivel",
            "veiculo_motor":        "Motor",
            "veiculo_chassi":       "Chassi Completo",
            "veiculo_renavam":      "Renavam",
            "veiculo_placa":        "Placa",
            "veiculo_patio":        "Patio",
            "veiculo_dias_patio":   "Dias Patio",
            "veiculo_situacao":     "Situação",
            "veiculo_nota_fabrica": "Nota Fábrica",
            "veiculo_emissao":      "Emissão",
            "veiculo_empresa":      "Empresa",
        }

        for chave, label in campos_veiculo.items():
            if chave == 'veiculo_modelo':
                dados[chave] = self._safe_get_text(

                    f"{veiculo_base}//label[normalize-space()='{label}']/following::label[2]"
                )
            else:
                dados[chave] = self._safe_get_text(

                    f"{veiculo_base}//label[normalize-space()='{label}']/following::label[1]"
                )
            

        # ── Ficha ─────────────────────────────────────────────────────
        prop_base = "//frm-detalhe-ficha"

        dados["ficha_tipo_evento"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Tipo Evento')]/following::label[1]"
        )
        dados["ficha_status"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Status')]/following::label[1]"
        )
        dados["ficha_empresa"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Empresa')]/following::label[1]"
        )
        dados["ficha_data_criacao"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Data Criação')]/following::label[1]"
        )
        dados["ficha_data_resgate"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Data Resgate')]/following::label[1]"
        )
        dados["ficha_data_fechamento"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Data Fechamento')]/following::label[1]"
        )
        dados["ficha_midea"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Mídia')]/following::label[1]"
        )
        
        dados["ficha_assunto"] = self._safe_get_text(
            f"{prop_base}//label[contains(text(),'Assunto')]/preceding::textarea[1]"
        )

        obs_button = self.driver.find_elements(*self._OBSERVATION_DETAILS)
        obs_button[1].click()

        lista_observacao = self.get_data_table()
        # Considera apenas a observação mais recente, que tenha as palavras "Pátio", " Trânsito" ou "Emplacamento"
        
        dados["ficha_observacao"] = self.extract_relevant_observation(lista_observacao)
    
        #CFOP será fixo porem quando houver a necessidade de alterar será informdo em observação
        dados['ficha_codigo_cfop'] = self.extract_cfop_from_observacao(lista_observacao)
        dados['veiculo_siminovo'] =  self.check_semi_novo_from_observacao(lista_observacao)
        dados['renvam_informado'] = self.extract_renavan_from_observacao(lista_observacao)
        dados['observacao_nbs'] = self.extract_obs_nbs_from_observacao(lista_observacao)
        dados['complemento_nbs'] = self.extract_complemento_nbs_from_observacao(lista_observacao)

        self.click(*self._CLOSE_OBSERVATION)

        return dados
    
    def extract_cfop_from_observacao(self, observacoes: list[dict]) -> str:
        for obs in observacoes:
            texto = obs.get("Observação", "")
            if "CFOP" in texto.upper():
                # Extrai o código CFOP usando uma expressão regular
                match = re.search(r'CFOP[:\s]*([0-9]+)', texto, re.IGNORECASE)
                if match:
                    return match.group(1)
        return "5405"  # Valor padrão caso CFOP não seja encontrado
    
    def extract_renavan_from_observacao(self, observacoes: list[dict]) -> str:
        for obs in observacoes:
            texto = obs.get("Observação", "")
            if "RENAVAN" in texto.upper():
                # Extrai o código RENAVAN usando uma expressão regular
                match = re.search(r'RENAVAN[\s]*([0-9]+)', texto, re.IGNORECASE)
                if match:
                    return str(match.group(1))
        return ""
    

    def extract_obs_nbs_from_observacao(self, observacoes: list[dict]) -> str:

        for obs in observacoes:
            texto = obs.get("Observação", "")

            match = re.search(
                r'(?:OBSERVA(?:ÇÃO|CAO)|OBS)\s*:\s*(.+)',
                texto,
                re.IGNORECASE
            )

            if match:
                return match.group(1).strip()

        return ""

    
    def extract_complemento_nbs_from_observacao(self, observacoes: list[dict]) -> str:
        for obs in observacoes:
            texto = obs.get("Observação", "")
            if "COMPL" in texto.upper():
                # Extrai o código COMPL: usando uma expressão regular
                import re
                match = re.search(r'COMPL[:\s]*([0-9]+)', texto, re.IGNORECASE)
                if match:
                    return str(match.group(1))
        return ""
    
    def check_semi_novo_from_observacao(self, observacoes: list[dict]) -> str:
        for obs in observacoes:
            texto = obs.get("Observação", "")
            if "SEMINOVA" in texto.upper() or "SEMINOVO" in texto.upper():
                return True
        return ''
    
    def extract_relevant_observation(self, observacoes: list[dict]) -> str:
        palavras_chave = ["pátio", "trânsito", "emplacamento", "patio", "transito"]
        for obs in observacoes:
            texto = obs.get("Observação", "")
            if any(palavra in texto.lower() for palavra in palavras_chave):
                return texto
        return ""

    def extract_rows(self) -> list[dict]:
        import time
        end = time.time() + 60

        itens = None
        while time.time() < end:
            try:
                itens = self.driver.find_elements(*self._TABLE_ROWS)
                if itens:
                    break
            except:
                pass
            self.sleep_withou_condition(3)
            
        if not itens:
            raise DataExtractionException("No rows found in NFs table.")
        
        resultados = []

        for item in itens:
            status = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, "label.nbs-tflabel")
            responsavel = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".responsavel-evento span")
            numero = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".font-semibold")
            cliente = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".cliente")
            tempo = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, "i.pi-clock + span")
            produto = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".vehicle span")

            try:
                info_extra = item.find_elements(By.CSS_SELECTOR, ".w-5 span")
                ano = info_extra[2].text.strip() if len(info_extra) > 2 else ""
            except:
                ano = ""

            item.click()
            self.sleep_withou_condition(3)
            detalhes = self.extrair_dados_ficha()
            close = self.driver.find_elements(*self._CLOSE_DATAILS)[1]
            close.click()
            self.sleep_withou_condition(3)

            resultados.append({
                "status": status,
                "responsavel": responsavel,
                "numero": numero,
                "cliente": cliente,
                "tempo": tempo,
                "produto": produto,
                "ano": ano,
                **detalhes
            })

        self.logger.info(f"Extracted {len(resultados)} NF(s) from current page")
        return resultados

    def get_data_table(self):
    
        tabela = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="gridPrincipalObservacao"]')
            )
        )

        # Cabeçalho 
        headers = tabela.find_elements(By.CSS_SELECTOR, "thead th")

        nomes_colunas = []
        for th in headers:
            if th.get_attribute("hidden"):
                continue

            titulo = th.text.strip()
            if titulo:
                nomes_colunas.append(titulo)

        # Linhas
        linhas = tabela.find_elements(By.CSS_SELECTOR, "tbody tr")

        dados = []

        for linha in linhas:
            colunas = linha.find_elements(By.CSS_SELECTOR, "td")

            valores = []
            for col in colunas:
                if col.get_attribute("hidden"):
                    continue

                texto = col.text.strip()
                valores.append(texto)

            if len(valores) == len(nomes_colunas):
                dados.append(dict(zip(nomes_colunas, valores)))

        return dados
    

    def clicar_evento_grid(self, numero_evento: str, timeout=10):

        # Aguarda o grid carregar
        registros = self.wait.until(
            EC.presence_of_all_elements_located((
                By.XPATH,
                '//div[contains(@class,"register-custom-grid")]'
            ))
        )

        for registro in registros:
            try:

                # Captura o número do evento
                elemento_evento = registro.find_element(
                    By.XPATH,
                    './/div[contains(@class,"column-evento")]//span[contains(@class,"lead")]'
                )

                evento = elemento_evento.text.strip()

                if evento == numero_evento:
                    # Clica na SEGUNDA COLUNA (container do evento)
                    coluna_evento = registro.find_element(
                        By.XPATH,
                        './/div[contains(@class,"column-evento")]'
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", coluna_evento)
                    self.driver.execute_script("arguments[0].click();", coluna_evento)

                    self.logger.info(f" Evento {numero_evento} encontrado e clicado.")
                    return True

            except Exception as e:
                continue

        self.logger.warning(f"Evento {numero_evento} não encontrado no grid.")
        return False
