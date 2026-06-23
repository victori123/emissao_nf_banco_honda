from src.logistics.pages.renave_emission_page import RenaveEmissionPage
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)

class RenaveEmissionFlow:
    def __init__(self, window):
        self.page = RenaveEmissionPage(window)

    def execute(self, chassi: str = ""):

        logger.info("Iniciando emissão de Renave")

        try:
            self.page.clicar_renave()
            mensagem = self.page.processar_operacao(chassi)
            
            if mensagem:
                logger.info("Mensagem de confirmação de Renave: %s", mensagem)

            logger.info("Renave emitido com sucesso")
            return mensagem

        except Exception:
            logger.error("Erro na emissão da Renave", exc_info=True)
            raise
