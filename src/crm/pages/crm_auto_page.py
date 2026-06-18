from selenium.webdriver.common.by import By
from src.crm.pages.base_crm_page import BaseCRMPage
from src.shared.exceptions.rpa_exceptions import DataExtractionException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

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

        self.click(*self._CLOSE_OBSERVATION)

        return dados
    
    def extract_relevant_observation(self, observacoes: list[dict]) -> str:
        palavras_chave = ["pátio", "trânsito", "emplacamento", "patio", "transito"]
        for obs in observacoes:
            texto = obs.get("Observação", "").lower()
            if any(palavra in texto for palavra in palavras_chave):
                return texto
        return ""

    def extract_rows(self) -> list[dict]:
        
        itens = self.driver.find_elements(*self._TABLE_ROWS)

        if not itens:
            raise DataExtractionException("No rows found in NFs table.")
        
        resultados = []

        for item in itens:
            status = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, "label.nbs-tflabel")
            responsavel = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".responsavel-evento span")
            numero = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".font-semibold")
            cliente = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".cliente")
            tempo = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, "i.pi-clock + span")
            email = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".trunk-text")
            produto = self._safe_get_text_element_on_memory(item, By.CSS_SELECTOR, ".vehicle span")

            try:
                info_extra = item.find_elements(By.CSS_SELECTOR, ".w-5 span")
                ano = info_extra[1].text.strip() if len(info_extra) > 1 else ""
                chassi = info_extra[2].text.strip() if len(info_extra) > 2 else ""
            except:
                ano = ""
                chassi = ""

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
                "email": email,
                "produto": produto,
                "ano": ano,
                "chassi": chassi,
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