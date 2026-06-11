from selenium.webdriver.common.by import By
from src.crm.pages.base_crm_page import BaseCRMPage
from src.shared.exceptions.rpa_exceptions import DataExtractionException

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

    _TABLE_ROWS = (By.CSS_SELECTOR, "custom-grid .body-grid .lista-dado")

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
        self.click(*self._ABA_PROPOSTA)
        self.click(*self._PESQUISAR)
        self.sleep_withou_condition(4)
        self.click(*self._PAINEL_AGUARDANDO_NF)

    def extract_rows(self) -> list[dict]:
        
        itens = self.driver.find_elements(*self._TABLE_ROWS)

        if not itens:
            raise DataExtractionException("No rows found in NFs table.")
        
        resultados = []

        for item in itens:
            try:
                status = item.find_element(By.CSS_SELECTOR, "label.nbs-tflabel").text.strip()
            except:
                status = ""

            try:
                responsavel = item.find_element(By.CSS_SELECTOR, ".responsavel-evento span").text.strip()
            except:
                responsavel = ""

            try:
                numero = item.find_element(By.CSS_SELECTOR, ".font-semibold").text.strip()
            except:
                numero = ""

            try:
                cliente = item.find_element(By.CSS_SELECTOR, ".cliente").text.strip()
            except:
                cliente = ""

            try:
                tempo = item.find_element(By.CSS_SELECTOR, "i.pi-clock + span").text.strip()
            except:
                tempo = ""

            try:
                email = item.find_element(By.CSS_SELECTOR, ".trunk-text").text.strip()
            except:
                email = ""

            try:
                produto = item.find_element(By.CSS_SELECTOR, ".vehicle span").text.strip()
            except:
                produto = ""

            try:
                info_extra = item.find_elements(By.CSS_SELECTOR, ".w-5 span")
                ano = info_extra[1].text.strip() if len(info_extra) > 1 else ""
                chassi = info_extra[2].text.strip() if len(info_extra) > 2 else ""
            except:
                ano = ""
                chassi = ""

            resultados.append({
                "status": status,
                "responsavel": responsavel,
                "numero": numero,
                "cliente": cliente,
                "tempo": tempo,
                "email": email,
                "produto": produto,
                "ano": ano,
                "chassi": chassi
            })

        self.logger.info(f"Extracted {len(resultados)} NF(s) from current page")
        return resultados
