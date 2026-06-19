from src.logistics.pages.nf_emission_page import NFEmissionPage
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)

class NFEmissionFlow:
    def __init__(self, window):
        self.page = NFEmissionPage(window)

    def execute(self, ficha_observacao: str = "", ficha_codigo_cfop: str = ""):

        logger.info("Iniciando emissão de NF")

        try:
            self.page.emitir_nf()
            self.page.preencher_dados_nota_fiscal(ficha_observacao, ficha_codigo_cfop)
            mensagem = self.page.confirmar()

            if mensagem:
                logger.info("Mensagem de confirmação da NF: %s", mensagem)

            logger.info("NF emitida com sucesso")
            return mensagem

        except Exception:
            logger.error("Erro na emissão da NF", exc_info=True)
            raise
