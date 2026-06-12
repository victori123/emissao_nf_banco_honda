from src.logistics.pages.chassis_search_page import ChassisSearchPage
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)
class ChassisSearchFlow:
    def __init__(self, window):
        self.page = ChassisSearchPage(window)

    def execute(self, chassis):

        logger.info(f"Buscando chassis: {chassis}")

        try:
            self.page.search(chassis)
            self.page.select_result()

            logger.info("Chassis localizado com sucesso")

        except Exception as e:
            logger.error(f"Erro na busca do chassis: {chassis}", exc_info=True)
            raise

