from src.logistics.pages.chassis_search_page import ChassisSearchPage
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)
class ChassisSearchFlow:
    def __init__(self, window):
        self.page = ChassisSearchPage(window)

    def execute(self, chassis):

        logger.info(f"Buscando chassis: {chassis}")

        try:
            self.page.clicar_propostas()
            self.page.search('9C2JC9710VR111202547')
            logger.info("Chassis localizado com sucesso")

        except Exception as e:
            logger.error(f"Erro na busca chassis: {chassis}", exc_info=True)
            raise
