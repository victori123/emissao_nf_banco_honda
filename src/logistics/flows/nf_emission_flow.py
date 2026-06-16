from src.logistics.pages.nf_emission_page import NFEmissionPage
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)

class NFEmissionFlow:
    def __init__(self, window):
        self.page = NFEmissionPage(window)

    def execute(self, ficha_observacao: str = ""):

        logger.info("Iniciando emissão de NF")

        try:
            self.page.emitir_nf()
            self.page.preencher_dados_nota_fiscal(ficha_observacao)
            self.page.confirmar()

            logger.info("NF emitida com sucesso")

        except Exception as e:
            logger.error("Erro na emissão da NF", exc_info=True)
            raise
